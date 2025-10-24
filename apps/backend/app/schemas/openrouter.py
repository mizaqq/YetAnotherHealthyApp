"""Pydantic contracts for interacting with the OpenRouter API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ChatRole(str, Enum):
    """Supported chat roles for OpenRouter messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class OpenRouterChatMessage(BaseModel):
    """Single message in a chat completion request or response."""

    role: ChatRole = Field(..., description="Role of the message author")
    content: str = Field(..., min_length=1, description="Message payload content")

    model_config = {"extra": "ignore", "str_strip_whitespace": True}


class JsonSchemaDefinition(BaseModel):
    """Definition of the JSON schema enforced by OpenRouter response_format."""

    name: str = Field(..., min_length=1, description="Identifier for the schema")
    strict: bool = Field(default=True, description="Enforces strict schema validation")
    schema: dict[str, Any] = Field(..., description="JSON Schema definition")

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_strict_is_true(self) -> "JsonSchemaDefinition":
        """Ensure strict mode is always enabled to guarantee deterministic responses."""

        if not self.strict:
            raise ValueError("json_schema.strict must be set to true for OpenRouter usage")
        return self


class JsonSchemaResponseFormat(BaseModel):
    """Represents OpenRouter JSON schema response format configuration."""

    type: Literal["json_schema"] = Field(default="json_schema")
    json_schema: JsonSchemaDefinition

    model_config = {"extra": "forbid"}


class OpenRouterChatRequest(BaseModel):
    """Payload contract sent to OpenRouter chat completions endpoint."""

    model: str = Field(..., min_length=1, description="Model identifier to use")
    messages: list[OpenRouterChatMessage] = Field(
        ..., min_length=1, description="Conversation history including latest user prompt"
    )
    response_format: JsonSchemaResponseFormat | None = Field(
        default=None,
        description="Optional response format enforcing structured outputs",
    )
    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
        description="Sampling temperature overriding configuration defaults",
    )
    top_p: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Nucleus sampling override",
    )
    max_output_tokens: int | None = Field(
        default=None,
        gt=0,
        description="Override for maximum completion tokens",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded to OpenRouter",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def ensure_assistant_message_not_last(self) -> "OpenRouterChatRequest":
        """Ensure the final message is not authored by the assistant."""

        if self.messages and self.messages[-1].role == ChatRole.ASSISTANT:
            raise ValueError("Last message in request must not be from assistant")
        return self


class StreamDelta(BaseModel):
    """Incremental update payload for streaming responses."""

    role: ChatRole | None = None
    content: str | None = None

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


class OpenRouterStreamChoice(BaseModel):
    """Single choice chunk emitted during streaming responses."""

    index: int = Field(..., ge=0)
    delta: StreamDelta
    finish_reason: str | None = None

    model_config = {"extra": "forbid"}


class OpenRouterStreamChunk(BaseModel):
    """Chunked streaming response contract from OpenRouter."""

    id: str
    model: str
    choices: list[OpenRouterStreamChoice]

    model_config = {"extra": "forbid"}


class UsageStats(BaseModel):
    """Token usage metrics for a completion response."""

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)

    model_config = {"extra": "ignore"}


class OpenRouterChatChoice(BaseModel):
    """Single response choice returned by OpenRouter."""

    index: int = Field(..., ge=0)
    message: OpenRouterChatMessage
    finish_reason: str | None = None

    model_config = {"extra": "ignore"}


class OpenRouterChatResponse(BaseModel):
    """Full chat completion response returned by OpenRouter."""

    id: str
    model: str
    created: int
    choices: list[OpenRouterChatChoice]
    usage: UsageStats | None = None

    model_config = {"extra": "ignore"}