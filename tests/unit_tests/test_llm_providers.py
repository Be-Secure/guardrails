import importlib.util
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from guardrails.llm_providers import (
    ArbitraryCallable,
    AsyncArbitraryCallable,
    LLMResponse,
    PromptCallableException,
    chat_prompt,
    get_llm_ask,
)

from .mocks import MockAsyncCustomLlm, MockCustomLlm


def test_arbitrary_callable_retries_on_retryable_errors(mocker):
    llm = MockCustomLlm()
    fail_retryable_spy = mocker.spy(llm, "fail_retryable")

    arbitrary_callable = ArbitraryCallable(llm.fail_retryable, prompt="Hello")
    response = arbitrary_callable()

    assert fail_retryable_spy.call_count == 2
    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


def test_arbitrary_callable_does_not_retry_on_non_retryable_errors(mocker):
    with pytest.raises(Exception) as e:
        llm = MockCustomLlm()
        fail_non_retryable_spy = mocker.spy(llm, "fail_non_retryable")

        arbitrary_callable = ArbitraryCallable(llm.fail_retryable, prompt="Hello")
        arbitrary_callable()

        assert fail_non_retryable_spy.call_count == 1
        assert isinstance(e, PromptCallableException) is True
        assert (
            str(e)
            == "The callable `fn` passed to `Guard(fn, ...)` failed with the following error: `Non-Retryable Error!`. Make sure that `fn` can be called as a function that takes in a single prompt string and returns a string."  # noqa
        )


def test_arbitrary_callable_does_not_retry_on_success(mocker):
    llm = MockCustomLlm()
    succeed_spy = mocker.spy(llm, "succeed")

    arbitrary_callable = ArbitraryCallable(llm.succeed, prompt="Hello")
    response = arbitrary_callable()

    assert succeed_spy.call_count == 1
    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


@pytest.mark.asyncio
async def test_async_arbitrary_callable_retries_on_retryable_errors(mocker):
    llm = MockAsyncCustomLlm()
    fail_retryable_spy = mocker.spy(llm, "fail_retryable")

    arbitrary_callable = AsyncArbitraryCallable(llm.fail_retryable, prompt="Hello")
    response = await arbitrary_callable()

    assert fail_retryable_spy.call_count == 2
    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


# Passing
@pytest.mark.asyncio
async def test_async_arbitrary_callable_does_not_retry_on_non_retryable_errors(mocker):
    with pytest.raises(Exception) as e:
        llm = MockAsyncCustomLlm()
        fail_non_retryable_spy = mocker.spy(llm, "fail_non_retryable")

        arbitrary_callable = AsyncArbitraryCallable(llm.fail_retryable, prompt="Hello")
        await arbitrary_callable()

        assert fail_non_retryable_spy.call_count == 1
        assert isinstance(e, PromptCallableException) is True
        assert (
            str(e)
            == "The callable `fn` passed to `Guard(fn, ...)` failed with the following error: `Non-Retryable Error!`. Make sure that `fn` can be called as a function that takes in a single prompt string and returns a string."  # noqa
        )


@pytest.mark.asyncio
async def test_async_arbitrary_callable_does_not_retry_on_success(mocker):
    llm = MockAsyncCustomLlm()
    succeed_spy = mocker.spy(llm, "succeed")

    arbitrary_callable = AsyncArbitraryCallable(llm.succeed, prompt="Hello")
    response = await arbitrary_callable()

    assert succeed_spy.call_count == 1
    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


@pytest.fixture(scope="module")
def openai_chat_mock():
    return {
        "choices": [
            {
                "message": {"content": "Mocked LLM output"},
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
        },
    }


@pytest.fixture(scope="module")
def openai_mock():
    return {
        "choices": [
            {
                "text": "Mocked LLM output",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
        },
    }


def test_openai_callable(mocker, openai_mock):
    mocker.patch("openai.Completion.create", return_value=openai_mock)

    from guardrails.llm_providers import OpenAICallable

    openai_callable = OpenAICallable()
    response = openai_callable(text="Hello")

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


@pytest.mark.asyncio
async def test_async_openai_callable(mocker, openai_mock):
    mocker.patch("openai.Completion.acreate", return_value=openai_mock)

    from guardrails.llm_providers import AsyncOpenAICallable

    openai_callable = AsyncOpenAICallable()
    response = await openai_callable(text="Hello")

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


def test_openai_chat_callable(mocker, openai_chat_mock):
    mocker.patch("openai.ChatCompletion.create", return_value=openai_chat_mock)

    from guardrails.llm_providers import OpenAIChatCallable

    openai_chat_callable = OpenAIChatCallable()
    response = openai_chat_callable(text="Hello")

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


@pytest.mark.asyncio
async def test_async_openai_chat_callable(mocker, openai_chat_mock):
    mocker.patch("openai.ChatCompletion.acreate", return_value=openai_chat_mock)

    from guardrails.llm_providers import AsyncOpenAIChatCallable

    openai_chat_callable = AsyncOpenAIChatCallable()
    response = await openai_chat_callable(text="Hello")

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


def test_openai_chat_model_callable(mocker, openai_chat_mock):
    mocker.patch("openai.ChatCompletion.create", return_value=openai_chat_mock)

    from guardrails.llm_providers import OpenAIChatCallable

    class MyModel(BaseModel):
        a: str

    openai_chat_model_callable = OpenAIChatCallable()
    response = openai_chat_model_callable(
        text="Hello",
        base_model=MyModel,
    )

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


@pytest.mark.asyncio
async def test_async_openai_chat_model_callable(mocker, openai_chat_mock):
    mocker.patch("openai.ChatCompletion.acreate", return_value=openai_chat_mock)

    from guardrails.llm_providers import AsyncOpenAIChatCallable

    class MyModel(BaseModel):
        a: str

    openai_chat_model_callable = AsyncOpenAIChatCallable()
    response = await openai_chat_model_callable(
        text="Hello",
        base_model=MyModel,
    )

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Mocked LLM output"
    assert response.prompt_token_count == 10
    assert response.response_token_count == 20


@pytest.mark.skipif(
    not importlib.util.find_spec("manifest"),
    reason="manifest-ml is not installed",
)
def test_manifest_callable():
    client = MagicMock()
    client.run.return_value = "Hello world!"

    from guardrails.llm_providers import ManifestCallable

    manifest_callable = ManifestCallable()
    response = manifest_callable(text="Hello", client=client)

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


@pytest.mark.skipif(
    not importlib.util.find_spec("manifest"),
    reason="manifest-ml is not installed",
)
@pytest.mark.asyncio
async def test_async_manifest_callable():
    client = MagicMock()

    async def return_async():
        return ["Hello world!"]

    client.arun_batch.return_value = return_async()

    from guardrails.llm_providers import AsyncManifestCallable

    manifest_callable = AsyncManifestCallable()
    response = await manifest_callable(text="Hello", client=client)

    assert isinstance(response, LLMResponse) is True
    assert response.output == "Hello world!"
    assert response.prompt_token_count is None
    assert response.response_token_count is None


class ReturnTempCallable(Callable):
    def __call__(*args, **kwargs) -> Any:
        return ""


@pytest.mark.parametrize(
    "llm_api, args, kwargs, expected_temperature",
    [
        (ReturnTempCallable(), [], {"temperature": 0.5}, 0.5),
        (ReturnTempCallable(), [], {}, 0),
    ],
)
def test_get_llm_ask_temperature(llm_api, args, kwargs, expected_temperature):
    result = get_llm_ask(llm_api, *args, **kwargs)
    assert "temperature" in result.init_kwargs
    assert result.init_kwargs["temperature"] == expected_temperature


def test_chat_prompt():
    # raises when neither msg_history or prompt are provided
    with pytest.raises(PromptCallableException):
        chat_prompt(None)
