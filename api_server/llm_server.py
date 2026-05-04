import logging
import os
import sys

from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark

load_dotenv()

sys.path.append(os.getcwd())

logger = logging.getLogger("LLM-Client")


def _to_plain_value(value: Any) -> Any:
    """Convert SDK response objects into JSON-serializable values.

    Args:
        value: Arbitrary value returned by the API SDK.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_plain_value(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _to_plain_value(value.model_dump())
    if hasattr(value, "dict"):
        return _to_plain_value(value.dict())
    if hasattr(value, "to_dict"):
        return _to_plain_value(value.to_dict())
    if hasattr(value, "__dict__"):
        return {
            str(key): _to_plain_value(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return str(value)


def _find_numeric_value(value: Any, target_keys: set[str]) -> int | float | str:
    """Find the first numeric value whose key matches any target key.

    Args:
        value: JSON-like object to search.
        target_keys: Candidate key names.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in target_keys and isinstance(item, (int, float)):
                return item
        for item in value.values():
            found = _find_numeric_value(item, target_keys = target_keys)
            if found != "":
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_numeric_value(item, target_keys = target_keys)
            if found != "":
                return found
    return ""


def _build_usage_metadata(usage: Any) -> Dict[str, Any]:
    """Build normalized usage metadata from an API usage object.

    Args:
        usage: Provider usage object or dictionary.
    """
    usage_dict = _to_plain_value(usage)
    if not isinstance(usage_dict, dict):
        usage_dict = {}

    prompt_tokens = _find_numeric_value(
        usage_dict,
        target_keys = {"prompt_tokens", "input_tokens"},
    )
    completion_tokens = _find_numeric_value(
        usage_dict,
        target_keys = {"completion_tokens", "output_tokens"},
    )
    reasoning_tokens = _find_numeric_value(
        usage_dict,
        target_keys = {"reasoning_tokens"},
    )
    total_tokens = _find_numeric_value(
        usage_dict,
        target_keys = {"total_tokens"},
    )
    if total_tokens == "" and isinstance(prompt_tokens, (int, float)) and isinstance(completion_tokens, (int, float)):
        total_tokens = prompt_tokens + completion_tokens

    return {
        "usage": usage_dict,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
    }


class LLM_Client:
    def __init__(
        self,
        mode: str = "ark",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: int = 300,
        print_stream: bool = True,
    ) -> None:
        mode_norm = (mode or "").strip().lower()
        if mode_norm in {"volcengine", "ark"}:
            self.mode = "ark"
        elif mode_norm in {"openai", "oai"}:
            self.mode = "openai"
        else:
            raise ValueError(f"Unsupported LLM mode: {mode!r}")

        if self.mode == "ark":
            resolved_api_key = api_key or os.environ.get("LLM_API_KEY")
            resolved_base_url = base_url or os.environ.get("LLM_API_BASE_URL")
        else:
            resolved_api_key = (
                api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
            )
            resolved_base_url = (
                base_url
                or os.environ.get("OPENAI_BASE_URL")
                or os.environ.get("OPENAI_API_BASE_URL")
                or os.environ.get("LLM_API_BASE_URL")
            )

        if not resolved_api_key:
            raise RuntimeError("Missing API key in environment or parameters.")

        self.api_key = resolved_api_key
        self.base_url = resolved_base_url
        self.default_model = default_model
        self.timeout = timeout
        self.print_stream = print_stream

        if self.mode == "ark":
            self._client = Ark(base_url=self.base_url, api_key=self.api_key)
        else:
            if self.base_url:
                self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            else:
                self._client = OpenAI(api_key=self.api_key)

    def chat(
        self,
        input_query: str,
        end_point: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        reasoning_option: Any = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
    ):
        model = end_point or self.default_model
        if not model:
            raise ValueError("Missing model/end_point.")

        if messages is None:
            assembled_messages = [{"role": "user", "content": input_query}]
            if system_prompt:
                assembled_messages = (
                    [{"role": "system", "content": system_prompt}] + assembled_messages
                )
        else:
            assembled_messages = messages

        resolved_extra_body = extra_body
        if resolved_extra_body is None:
            if self.mode == "ark":
                if isinstance(reasoning_option, dict):
                    resolved_extra_body = reasoning_option
                elif isinstance(reasoning_option, str):
                    resolved_extra_body = {"thinking": {"type": reasoning_option}}
                elif isinstance(reasoning_option, bool):
                    resolved_extra_body = {
                        "thinking": {"type": "enabled" if reasoning_option else "disabled"}
                    }
            elif self.mode == "openai":
                if isinstance(reasoning_option, dict):
                    resolved_extra_body = reasoning_option
                elif isinstance(reasoning_option, str):
                    if reasoning_option in {"enabled", "on", "true"}:
                        effort = "low"
                    elif reasoning_option in {"disabled", "off", "false"}:
                        effort = "none"
                    else:
                        effort = reasoning_option
                    resolved_extra_body = {"reasoning": {"effort": effort}}
                elif isinstance(reasoning_option, bool):
                    if reasoning_option:
                        resolved_extra_body = {"reasoning": {"effort": "low"}}
                    else:
                        model_norm = str(model).strip().lower()
                        if model_norm.startswith(("gpt-5", "o")):
                            resolved_extra_body = {"reasoning": {"effort": "none"}}

        create_kwargs = {
            "model": model,
            "messages": assembled_messages,
            "timeout": timeout if timeout is not None else self.timeout,
            "stream": stream,
        }
        if temperature is not None:
            create_kwargs["temperature"] = float(temperature)
        if top_p is not None:
            create_kwargs["top_p"] = float(top_p)
        if max_tokens is not None:
            create_kwargs["max_tokens"] = int(max_tokens)
        if resolved_extra_body is not None:
            create_kwargs["extra_body"] = resolved_extra_body

        try:
            if (
                self.mode == "openai"
                and isinstance(resolved_extra_body, dict)
                and "reasoning" in resolved_extra_body
            ):
                try:
                    reasoning = resolved_extra_body.get("reasoning")
                    extra_passthrough = dict(resolved_extra_body)
                    extra_passthrough.pop("reasoning", None)

                    response_kwargs = {
                        "model": model,
                        "input": assembled_messages,
                        "reasoning": reasoning,
                        "timeout": timeout if timeout is not None else self.timeout,
                        "stream": stream,
                    }
                    if temperature is not None:
                        response_kwargs["temperature"] = float(temperature)
                    if top_p is not None:
                        response_kwargs["top_p"] = float(top_p)
                    if max_tokens is not None:
                        response_kwargs["max_output_tokens"] = int(max_tokens)
                    if extra_passthrough:
                        response_kwargs["extra_body"] = extra_passthrough

                    response = self._client.responses.create(**response_kwargs)
                    if stream:
                        result = ""
                        for event in response:
                            delta = getattr(event, "delta", None)
                            if isinstance(delta, str) and delta:
                                logger.info(delta)
                                result += delta
                                if self.print_stream:
                                    print(delta, end="")
                            else:
                                text = getattr(event, "text", None)
                                if isinstance(text, str) and text:
                                    logger.info(text)
                                    result += text
                                    if self.print_stream:
                                        print(text, end="")
                    else:
                        result = getattr(response, "output_text", None)
                        if not result and hasattr(response, "output"):
                            output = getattr(response, "output", None)
                            if isinstance(output, list):
                                result = "".join(
                                    str(item.get("text", ""))
                                    for item in output
                                    if isinstance(item, dict) and item.get("type") == "output_text"
                                )

                    reasoning_content = ""
                    usage = getattr(response, "usage", None)
                    usage_metadata = _build_usage_metadata(usage)
                    prompt_tok = usage_metadata["prompt_tokens"]
                    completion_tok = usage_metadata["completion_tokens"]

                    if not isinstance(result, str):
                        result = "dummy_result"

                    return reasoning_content, result, prompt_tok, completion_tok, usage_metadata
                except Exception as e:
                    logger.error(e)
                    fallback_kwargs = dict(create_kwargs)
                    fb_extra = fallback_kwargs.get("extra_body")
                    if isinstance(fb_extra, dict):
                        fb_extra = dict(fb_extra)
                        fb_extra.pop("reasoning", None)
                        if fb_extra:
                            fallback_kwargs["extra_body"] = fb_extra
                        else:
                            fallback_kwargs.pop("extra_body", None)
                    completion = self._client.chat.completions.create(**fallback_kwargs)
            else:
                completion = self._client.chat.completions.create(**create_kwargs)
            if stream:
                result = ""
                for tok in completion:
                    choices = getattr(tok, "choices", None)
                    if not choices:
                        continue
                    delta = getattr(choices[0], "delta", None)
                    content_piece = None
                    if delta is not None:
                        content_piece = getattr(delta, "content", None)
                    if not content_piece:
                        continue
                    logger.info(content_piece)
                    result += content_piece
                    if self.print_stream:
                        print(content_piece, end="")
            else:
                result = completion.choices[0].message.content

            try:
                message = completion.choices[0].message
                reasoning_content = getattr(message, "reasoning_content", "") or ""
            except Exception as e:
                logger.error(f"Error extracting reasoning_content: {e}")
                reasoning_content = ""

            usage_metadata = _build_usage_metadata(getattr(completion, "usage", None))
            prompt_tok = usage_metadata["prompt_tokens"]
            completion_tok = usage_metadata["completion_tokens"]

            if not stream:
                # logger.info(f"result: {result}")
                # logger.info("No Streaming") 
                pass

            if not isinstance(result, str):
                result = "dummy_result"
                reasoning_content = ""
                prompt_tok, completion_tok = "", ""
                usage_metadata = _build_usage_metadata(None)

            return reasoning_content, result, prompt_tok, completion_tok, usage_metadata
        except Exception as e:
            logger.error(e)
            return None, "dummy_result", "", "", _build_usage_metadata(None)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()],
    )

    client =  LLM_Client(
        mode = "ark",
        api_key = os.environ.get("WORKER_API_KEY"),
        base_url = os.environ.get("WORKER_BASE_URL"),
        default_model = os.environ.get("WORKER_MODEL_NAME"),
    )
    reasoning_content, result, prompt_tok, completion_tok, usage_metadata = client.chat(
        input_query = "你好",
        end_point = os.environ.get("WORKER_MODEL_NAME"),
        reasoning_option = False,
    )
    logger.info(result)



    client = LLM_Client(
        mode = "openai",
        api_key = os.environ.get("WORKER_API_KEY"),
        base_url = os.environ.get("WORKER_BASE_URL"),
        default_model = os.environ.get("WORKER_MODEL_NAME"),
    )
    reasoning_content, result, prompt_tok, completion_tok, usage_metadata = client.chat(
        input_query = "你好",
        end_point = os.environ.get("WORKER_MODEL_NAME"),
        reasoning_option = False,   
    )
    logger.info(reasoning_content)
    logger.info(result)
