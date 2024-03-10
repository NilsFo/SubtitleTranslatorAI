import json
import os
import time

import openai

import initial_prompt
from util import log, utils


class GPTResponseData:

    def __init__(self, original_prompt: str, predictions):
        # arguments
        self.original_prompt: str = original_prompt
        self.response_timestamp: int = time.time_ns()

        # extracting dict fields
        self.openai_id: str = predictions.openai_id
        self.organization: str = predictions.organization
        self.response_ms: int = predictions.response_ms
        self.id: str = predictions.id
        self.object: str = predictions.object
        self.created: int = predictions.created
        self.model: str = predictions.model

        # extracting token info
        self.prompt_tokens: int = predictions.usage.prompt_tokens
        self.completion_tokens: int = predictions.usage.completion_tokens
        self.total_tokens: int = predictions.usage.total_tokens

        # extracting choices
        choices = predictions.choices

        # selecting a choice to use
        self.selected_choice_index: int = 0

        answer = choices[self.selected_choice_index]
        message = answer.message
        self.finish_reason: str = answer.finish_reason
        self.answer_role: str = message.role
        self.answer_content: str = message.content

        # summary
        self.summary_json: str = json.dumps(predictions.to_dict_recursive(), indent=2)
        self.message_json: str = json.dumps(message.to_dict_recursive(), indent=2)

    def to_dict(self) -> {}:
        summary = json.loads(self.summary_json)
        message = json.loads(self.message_json)
        d = {
            # Class fields
            'timestamp': self.response_timestamp,
            'original_prompt': self.original_prompt,
            'organization': self.organization,
            'openai_id': self.openai_id,
            'response_ms': self.response_ms,
            'id': self.id,
            'object': self.object,
            'created': self.created,
            'model': self.model,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'selected_choice_index': self.selected_choice_index,
            'answer.finish_reason': self.finish_reason,
            'message_role': self.answer_role,
            'message_content': self.answer_content,

            # Summaries
            'summary': summary,
            'message': message
        }

        return d

    def answer_created_without_problems(self) -> bool:
        return self.finish_reason.strip().lower() == 'stop'.strip().lower()

    def to_json(self, indent: int = 2) -> str:
        return str(json.dumps(self.to_dict(), indent=indent))

    def dump_response(self, out_dir: str, indent: int = 2):
        json_dump = self.to_json(indent=indent)
        json_dump = str(json_dump)
        h = hash(json_dump)
        h = abs(h)

        os.makedirs(out_dir, exist_ok=True)
        out_file_name = out_dir + os.sep + 'gpt_response_dump-' + str(self.id) + '-' + str(h) + '.json'
        f = open(out_file_name, 'w', encoding="utf-8")
        f.write(json_dump)
        f.close()

    def __str__(self) -> str:
        return self.to_json()


class TranslationGPT:

    def __init__(self,
                 api_key: str,
                 output_language: str,
                 output_country: str,
                 gpt_model_name: str = 'gpt-3.5-turbo'):
        assert api_key is not None
        assert output_language is not None
        assert output_country is not None

        log.write('Setting up ChatGPT model.')
        log.write('OpenAI API Key: ' + utils.chat_gpt_api_key_printable(api_key))

        # Setting fields
        openai.api_key = api_key
        self.gpt_model_name = str(gpt_model_name)
        self.output_language = str(output_language)
        self.output_country = str(output_country)
        self.session_history = None
        self.tokens_asked = 0
        self.tokens_generated = 0

        # Setting up Model
        self.clear_session()

    def create_initial_prompt(self) -> str:
        return initial_prompt.get_prompt(language=self.output_language, country=self.output_country)

    def clear_session(self):
        self.session_history = [{'role': 'system', 'content': self.create_initial_prompt()}]
        self.tokens_generated = 0
        self.tokens_asked = 0

    def prompt_model(self,
                     # The new string to send to the model. The model will reply based on the current history.
                     prompt: str,

                     # ================
                     # MODEL PARAMETERS
                     # ================
                     temperature: float = 1.0,
                     # The default temperature value is 1.0. Higher values (e.g., 1.5) make the output more random,
                     # while lower values (e.g., 0.2) make the output more focused and deterministic.

                     top_p: float = 1.0,
                     # The default value is 1.0, which means all tokens are considered for sampling.
                     # Setting it to a lower value (e.g., 0.8) restricts the sampling to the top cumulative
                     # probability until the specified probability mass is reached.

                     frequency_penalty: float = 0.0,
                     # The default value is 0.0, meaning no penalty is applied based on token frequency.
                     # You can set it to a positive value (e.g., 0.2) to encourage the model to be
                     # more diverse in its word choices

                     presence_penalty: float = 0.0,
                     # The default value is 0.0, meaning no penalty is applied for repeated words or phrases in the
                     # output. You can set it to a positive value (e.g., 0.2) to discourage the model from
                     # repeating the same phrases

                     print_to_console: bool = False
                     # silent. If true, nothing is printed into the console. Logs are still logged.
                     ):
        # Checking if function can be called
        if self.session_history is None:
            raise AttributeError('The model did not receive an initial prompt. Please setup session first!')
        if prompt is None:
            raise TypeError('Illegal prompt: "' + str(prompt) + '"!')
        prompt = str(prompt).strip()

        # logging
        log.write('Prompting Model: "' + prompt + '".', print_to_console=print_to_console)

        # Creating the prompt history
        # and choosing
        self.session_history.append({'role': 'user', 'content': prompt})
        predictions = openai.ChatCompletion.create(
            # setting model parameters
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,

            # choosing model name
            model=self.gpt_model_name,
            # providing the 'chat history'
            messages=self.session_history
        )

        out_dir = log.log_dir_base + os.sep + 'log' + os.sep + 'model'
        os.makedirs(out_dir, exist_ok=True)

        # Manage Response
        gpt_response = GPTResponseData(original_prompt=prompt, predictions=predictions)
        gpt_response.dump_response(out_dir=out_dir)
        log.write('GPT responded in ' + str(gpt_response.response_ms) + ' ms', print_to_console=print_to_console)
        log.write('GPT response: "' + gpt_response.answer_content + '"', print_to_console=print_to_console)

        # History
        self.session_history.append({'role': 'assistant', 'content': gpt_response.answer_content})
        self.tokens_generated = self.tokens_generated + gpt_response.completion_tokens
        self.tokens_asked = self.tokens_asked + gpt_response.prompt_tokens
        return gpt_response

    def prompt_history(self) -> [{}]:
        history = []
        for d in self.session_history:
            history.append({
                'role': d['role'],
                'content': d['content']
            })
        return history

    def prompt_history_json(self, indent: int = 2) -> str:
        return json.dumps(self.prompt_history(), indent=indent)

    def translate_line(self, line: str, silent: bool = False) -> [str, GPTResponseData]:
        gpt_response = self.prompt_model(prompt=line, print_to_console=not silent)
        translated_line = gpt_response.answer_content
        return utils.remove_quotations(translated_line), gpt_response
