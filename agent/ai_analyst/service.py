"""Service orchestrator for AI Financial Analyst queries."""

import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from agent.ai_analyst.context import build_portfolio_analytics_context
from agent.ai_analyst.prompts import SYSTEM_PROMPT, build_analyst_user_prompt
from agent.ai_analyst.schemas import AnalystResponse
from agent.stock_analysis import get_llm_client, get_llm_model

logger = logging.getLogger(__name__)


class FinancialAnalystService:
    """Service layer managing deterministic context retrieval and grounded LLM explanations."""

    def __init__(self, client=None, model: Optional[str] = None):
        self._client = client
        self._model = model

    def _get_client(self):
        if self._client is not None:
            return self._client
        return get_llm_client()

    def _get_model(self) -> str:
        if self._model is not None:
            return self._model
        return get_llm_model()

    def ask(
        self,
        portfolio_id: str,
        question: str,
        session: Session,
    ) -> AnalystResponse:
        """Process user inquiry with deterministic grounding and LLM interpretation."""
        # 1. Validate portfolio ID
        try:
            p_uuid = uuid.UUID(str(portfolio_id).strip())
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid portfolio ID '{portfolio_id}'. Must be a valid UUID format.",
            )

        # 2. Validate question
        clean_q = str(question).strip() if question else ""
        if not clean_q:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty or contain only whitespace.",
            )
        if len(clean_q) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question exceeds maximum allowed length of 1000 characters (received {len(clean_q)}).",
            )

        # 3. Retrieve deterministic analytics context
        try:
            context = build_portfolio_analytics_context(session, p_uuid)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to assemble portfolio analytics context: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while compiling deterministic portfolio analytics.",
            )

        # 4. Assemble system and user prompts
        context_str = context.to_prompt_text()
        user_prompt = build_analyst_user_prompt(context_str, clean_q)

        # 5. Call configured LLM provider
        try:
            client = self._get_client()
            model_name = self._get_model()

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except ValueError as e:
            # Missing API keys or unsupported provider
            logger.warning("LLM provider configuration error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Analyst provider is not configured. Please ensure valid LLM API keys are set.",
            )
        except Exception as e:
            # Network timeout, rate limit, or provider error
            logger.error("LLM provider execution error: %s", type(e).__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI Analyst provider was unable to generate a response. Please try again later.",
            )

        # 6. Parse and validate LLM output
        try:
            raw_answer = response.choices[0].message.content
            clean_answer = str(raw_answer).strip() if raw_answer else ""
        except (AttributeError, IndexError):
            clean_answer = ""

        if not clean_answer:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI Analyst provider returned an empty or malformed response.",
            )

        return AnalystResponse(
            question=clean_q,
            answer=clean_answer,
            portfolio_id=str(p_uuid),
            metrics_used=context.metrics_available,
            warnings=context.warnings,
        )
