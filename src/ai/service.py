from typing import Dict, List, Optional, Union
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from openai import OpenAI
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
from pathlib import Path
import openai

from src.ai.schemas import (
    AiTranslationCreateModel,
    AiTranslationResponseModel,
    SpeechDetails,
    AiTranslationServiceResultModel,
    TtsCreateModel,
    AiSpeakerServiceResponseModel,
    AiSpeakerServiceSpeaker,
    AiSpeakerServiceSpeakerInformation,
    AiSpeakerServiceSpeakersDetails,
    Segment,
)
import os

load_dotenv()


class AiService:
    def tts_service(self, tts_data: TtsCreateModel):
        print("Sent audio" + tts_data.filepath)
        with openai.audio.speech.with_streaming_response.create(
            # model="gpt-4o-mini-tts",
            model="tts-1",
            # voice=tts_data.voice,
            voice=tts_data.voice,
            input=tts_data.speech_transcript,
        ) as response:
            print("Saving audio" + tts_data.filepath)

            response.stream_to_file(f"{tts_data.filepath}.mp3")
        return f"{tts_data.filepath}.mp3"

    async def translation_service(self, speechDet: AiTranslationCreateModel):

        client = OpenAI()
        # model = OpenAIModel("gpt-4o-mini")
        # model = OpenAIModel("gpt-4o")
        model = OpenAIModel(
            "grok-3-beta",
            provider=OpenAIProvider(
                base_url="https://api.x.ai/v1",
                api_key=os.getenv("XAI_API_KEY"),
            ),
        )

        data = speechDet.transcript
        speech = SpeechDetails(
            title=speechDet.title,
            speakers=speechDet.speakers,
            number_of_speakers=speechDet.speaker_number,
            context=speechDet.context,
        )

        # Standalone Markdown function
        def to_markdown(speech: SpeechDetails) -> str:
            # Initialize Markdown string
            markdown = []

            # Add title
            markdown.append(f"**Title**: {speech.title}")

            # Add type
            markdown.append(f"**Type**: {speech.stype}")

            # Add number of speakers
            markdown.append(f"**Number of Speakers**: {speech.number_of_speakers}")

            # Add speakers list
            markdown.append("**Speakers**:")
            for index, speaker in enumerate(speech.speakers, 1):
                markdown.append(f"{index}. **Name**: {speaker.name}")
                markdown.append(f"   **Info**: {speaker.info}")

            # Add context if present
            if speech.context is not None:
                markdown.append(f"**Context**: {speech.context}")

            # Join lines with newlines
            return "\n".join(markdown)

        gpt4_agent = Agent(
            model=model,
            result_type=AiTranslationResponseModel,
            deps_type=SpeechDetails,
            retries=3,
            system_prompt="You are an intelligent and helpful AI agent. "
            "Analyze queries carefully and provide structured responses. "
            "Use context to look up relevant info. Strictly adhere to the provided response model.",
        )

        @gpt4_agent.system_prompt
        async def add_customer_name(ctx: RunContext[SpeechDetails]) -> str:
            return f"Speech details: {to_markdown(ctx.deps)}"

        newData = data.split(" ")
        resultList: List[Segment] = []
        index = 0
        window = 500
        overlap = 100
        indexIncrease = window - overlap
        summariesList: List[str] = []

        first_prompt = (
            "Please attribute the different speakers of the following youtube transcript. Return the full content for all of the speakers in segments, infer content if there seem to be grammatical errors. Use the provided context to decide how many speakers there are, and who likely said what."
            + "Since the context window of you as an AI agent is limited, you will receive about "
            + str(window)
            + " words at a time or less, please perform speaker distribution on as much of the text as you can. There will be an overlap of 100 words (meaning i will send words 0-"
            + str(window)
            + " for request 1, then words "
            + str(indexIncrease)
            + "-"
            + str(indexIncrease + window)
            + " for request 2, then words "
            + str(indexIncrease * 2)
            + "- "
            + str(indexIncrease * 2 + window)
            + " for request 3, etc). "
        )

        prompt = (
            "Please attribute the different speakers of the following youtube transcript. Return the full content for all of the speakers in segments, infer content if there seem to be grammatical errors. Use the provided context to decide how many speakers there are, and who likely said what."
            + "Since the context window of you as an AI agent is limited, you will receive about "
            + str(window)
            + " words at a time or less, please perform speaker distribution on as much of the text as you can. There will be an overlap of 100 words (meaning i will send words 0-"
            + str(window)
            + " for request 1, then words "
            + str(indexIncrease)
            + "-"
            + str(indexIncrease + window)
            + " for request 2, then words "
            + str(indexIncrease * 2)
            + "- "
            + str(indexIncrease * 2 + window)
            + " for request 3, etc). You will also be provided with the last segment that you produced. Rework that segment with the new words you receive first. Then work on the rest of the text sent to you as well. Strictly adhere to the response model provided, donot return extra information. Here is the content of the last segment:"
        )
        last_segment = "No last segment for this request"

        response = await gpt4_agent.run(
            first_prompt
            + "\n\n The next chunk of the text is here: "
            + " ".join(newData[index : index + window]),
            deps=speech,
        )
        last_segment = response.data.speaker_attribution[-1]
        index += indexIncrease
        resultList.extend(response.data.speaker_attribution[:-1])
        summariesList.append(response.data.summary_in_vietnamese)
        print(response.data)

        while index + window < len(newData):
            response = await gpt4_agent.run(
                prompt
                + last_segment.model_dump_json(indent=2)
                + ". Here is the context you recorded: "
                + response.data.what_to_notice_for_the_request
                + "\n\n The next chunk of the text is here: "
                + " ".join(newData[index : index + window]),
                deps=speech,
            )

            index += indexIncrease
            last_segment = response.data.speaker_attribution[-1]
            resultList.extend(response.data.speaker_attribution[:-1])
            summariesList.append(response.data.summary_in_vietnamese)
            print(response.data)

        response = await gpt4_agent.run(
            prompt
            + last_segment.model_dump_json(indent=2)
            + ". Here is the context you recorded: "
            + response.data.what_to_notice_for_the_request
            + "\n\n The next chunk of the text is here: "
            + " ".join(newData[index:]),
            deps=speech,
        )
        print(response.data)

        summariesList.append(response.data.summary_in_vietnamese)
        resultList.extend(response.data.speaker_attribution)

        summariesResponse = await gpt4_agent.run(
            "For AI agent: You have finished working with the text/transcript. Thank you so much! Now, I will give you a list of summaries that you have produced for the whole text. Rewrite those into a more detailed summary. Here are all the summaries produced: "
            + " ".join(summariesList)
            + "Strictly comply with the response format given.",
            deps=speech,
        )
        print(summariesResponse.data)

        # response = await gpt4_agent.run(prompt + " Start here: " + data, deps=speech)

        # print(response.all_messages())

        # print(response.data.model_dump_json(indent=2))
        print("----------------------------------------------------\n\n\n\n")
        # resultTranslation = []
        # for segment in resultList:
        #     resultTranslation.append(segment.original_speech)

        # print(resultTranslation)
        response.data.summary_in_vietnamese = (
            summariesResponse.data.summary_in_vietnamese
        )

        print("Speech details:\n" f"Summary: {response.data.summary_in_vietnamese}\n ")

        # print(f"./{response.data.short_title}.txt")

        # with open(f"{response.data.short_title}.txt", "w", encoding="utf-8") as f:
        #     with open(f"{response.data.short_title}_vi.txt", "w", encoding="utf-8") as f2:
        #         for segment in response.data.speaker_attribution:
        #             f.write(
        #                 segment.speaker_name + "... " + segment.original_speech + "\n\n"
        #             )
        #             f2.write(
        #                 segment.speaker_name + "... " + segment.translation_vi + "\n\n"
        #             )
        ttsData: List[str] = []
        translatedData: List[str] = []
        attributedData: List[str] = []
        speakerName = ""
        for segment in resultList:

            if speakerName == segment.speaker_name:
                speakerName = ""
            else:
                speakerName = segment.speaker_name + " nói: "

            ttsData.append(
                "[Pause] " + speakerName + segment.translation_vi + " [Pause]"
            )

            translatedData.append(speakerName + segment.translation_vi + "\n")
            attributedData.append(speakerName + segment.original_speech + "\n")
            speakerName = segment.speaker_name

        print("".join(attributedData))

        # for segment in resultList:

        # return AiTranslationServiceResultModel(
        #     ai_response=response.data,
        #     attributed_speech="".join(attributedData),
        #     translated_speech="".join(translatedData),
        #     translated_speech_for_tts="".join(ttsData),
        # )

        return AiTranslationServiceResultModel(
            ai_response=response.data,
            attributed_speech="".join(attributedData),
            translated_speech="".join(translatedData),
            translated_speech_for_tts=ttsData,
        )

        # return None

    async def speaker_service(
        self, speakers: AiSpeakerServiceSpeakersDetails, language: str = "Vietnamese"
    ):
        def to_markdown(
            obj: Union[AiSpeakerServiceSpeaker, AiSpeakerServiceSpeakersDetails],
        ) -> str:
            """
            Convert a Speaker or Speakers_details instance to Markdown format.

            Args:
                obj: A Speaker or Speakers_details instance.

            Returns:
                A string containing the Markdown representation.

            Raises:
                ValueError: If the input is neither a Speaker nor a Speakers_details instance.
            """
            if isinstance(obj, AiSpeakerServiceSpeaker):
                markdown = f"### Speaker\n"
                markdown += f"- **Name**: {obj.name}\n"
                markdown += f"- **Organization**: {obj.organization}\n"
                if obj.extra_information:
                    markdown += f"- **Extra Information**: {obj.extra_information}\n"
                return markdown.strip()

            elif isinstance(obj, AiSpeakerServiceSpeakersDetails):
                markdown = f"# Speakers Details\n"
                markdown += f"**Number of Speakers**: {obj.number_of_speakers}\n"
                # if obj.conteexxt:
                #     markdown += f"**Context**: {obj.context}\n"
                markdown += "\n## Speakers List\n"
                for i, speaker in enumerate(obj.speakers, 1):
                    markdown += f"### Speaker {i}\n"
                    # Generate speaker Markdown and remove redundant heading
                    speaker_markdown = to_markdown(speaker).replace("### Speaker\n", "")
                    markdown += speaker_markdown + "\n\n"
                return markdown.strip()

            else:
                raise ValueError("Input must be a Speaker or Speakers_details instance")

        client = OpenAI()
        model = OpenAIModel(
            "grok-3-mini-beta",
            provider=OpenAIProvider(
                base_url="https://api.x.ai/v1",
                api_key=os.getenv("XAI_API_KEY"),
            ),
        )
        # model = OpenAIModel("gpt-4o")

        gpt4_agent = Agent(
            model=model,
            result_type=AiSpeakerServiceResponseModel,
            deps_type=AiSpeakerServiceSpeakersDetails,
            retries=3,
            system_prompt="You are an intelligent and helpful AI agent. "
            "Analyze queries carefully and provide structured responses. "
            "Use context to look up relevant info",
        )

        @gpt4_agent.system_prompt
        async def speakers_context(
            ctx: RunContext[AiSpeakerServiceSpeakersDetails],
        ) -> str:
            return f"Speakers' details: {to_markdown(ctx.deps)}"

        print(to_markdown(speakers))

        prompt = (
            "Please give me accurate information (in "
            + language
            + ") about the following speakers (who are speaking in a transcript). Be specific and search up datails and DONOT BE GENERAL. If the given name has tiny mistake, correct the mistake in the response"
        )
        response = await gpt4_agent.run(prompt, deps=speakers)

        response.all_messages()

        print(response.data.model_dump_json(indent=2))

        return response.data
