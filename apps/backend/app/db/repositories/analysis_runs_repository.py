"""Repository for accessing analysis runs data."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

from supabase import Client

logger = logging.getLogger(__name__)


class AnalysisRunsRepository:
    """Data access layer for analysis runs stored in Supabase."""

    _ANALYSIS_RUNS_TABLE: Final[str] = "analysis_runs"
    _MEALS_TABLE: Final[str] = "meals"

    _DETAIL_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "meal_id",
        "run_no",
        "status",
        "latency_ms",
        "tokens",
        "cost_minor_units",
        "cost_currency",
        "threshold_used",
        "model",
        "retry_of_run_id",
        "error_code",
        "error_message",
        "created_at",
        "completed_at",
    )

    _QUEUED_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "meal_id",
        "run_no",
        "status",
        "threshold_used",
        "model",
        "retry_of_run_id",
        "latency_ms",
        "created_at",
    )

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client.

        Args:
            supabase_client: Configured Supabase client instance
        """
        self._client = supabase_client

    async def get_by_id(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Retrieve a single analysis run by ID for a specific user.

        Fetches only metadata fields (excludes raw_input/raw_output for security).
        Filters by both run_id and user_id to enforce row-level authorization.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier (for authorization via RLS)

        Returns:
            Analysis run record dict with parsed types, or None if not found

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .select(",".join(self._DETAIL_COLUMNS))
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.debug(
                    "Analysis run not found or not authorized",
                    extra={"run_id": str(run_id), "user_id": str(user_id)},
                )
                return None

            record = response.data[0]
            return self._normalize_analysis_run_record(record)

        except Exception as exc:
            logger.exception(
                "Failed to fetch analysis run: %s for user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to fetch analysis run: {exc}") from exc

    async def get_run_with_raw_input(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Retrieve an analysis run with raw_input for retry operations.

        Fetches all detail fields plus raw_input (excludes raw_output).
        Used specifically for retry operations where we need source run's input.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier (for authorization via RLS)

        Returns:
            Analysis run record dict with raw_input, or None if not found

        Raises:
            RuntimeError: If database query fails
        """
        try:
            columns = list(self._DETAIL_COLUMNS) + ["raw_input"]
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .select(",".join(columns))
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.debug(
                    "Analysis run not found or not authorized",
                    extra={"run_id": str(run_id), "user_id": str(user_id)},
                )
                return None

            record = response.data[0]
            normalized = self._normalize_analysis_run_record(record)
            # Add raw_input which is not in _normalize_analysis_run_record
            normalized["raw_input"] = record.get("raw_input")
            return normalized

        except Exception as exc:
            logger.exception(
                "Failed to fetch analysis run with raw_input: %s for user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to fetch analysis run: {exc}") from exc

    @staticmethod
    def _normalize_analysis_run_record(record: dict[str, Any]) -> dict[str, Any]:
        """Normalize analysis run record with proper type conversions.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with Python types (UUID, datetime, Decimal)

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "meal_id", "run_no", "status", "model", "created_at"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Analysis run record missing required fields: {missing}")

        # Parse datetime fields
        created_at = record["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        completed_at = None
        if record.get("completed_at"):
            completed_at = record["completed_at"]
            if isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "meal_id": (
                UUID(record["meal_id"]) if isinstance(record["meal_id"], str) else record["meal_id"]
            ),
            "run_no": record["run_no"],
            "status": record["status"],
            "latency_ms": record.get("latency_ms"),
            "tokens": record.get("tokens"),
            "cost_minor_units": record.get("cost_minor_units"),
            "cost_currency": record.get("cost_currency", "USD"),
            "threshold_used": (
                Decimal(str(record["threshold_used"]))
                if record.get("threshold_used") is not None
                else None
            ),
            "model": record["model"],
            "retry_of_run_id": (
                UUID(record["retry_of_run_id"]) if record.get("retry_of_run_id") else None
            ),
            "error_code": record.get("error_code"),
            "error_message": record.get("error_message"),
            "created_at": created_at,
            "completed_at": completed_at,
        }

    async def get_meal_for_user(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Validate that a meal exists and belongs to the user.

        Args:
            meal_id: Meal identifier to validate
            user_id: User identifier for authorization

        Returns:
            Meal record dict with id, user_id, deleted_at, or None if not found

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table(self._MEALS_TABLE)
                .select("id,user_id,deleted_at")
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .is_("deleted_at", "null")
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.debug(
                    "Meal not found or not authorized",
                    extra={"meal_id": str(meal_id), "user_id": str(user_id)},
                )
                return None

            record = response.data[0]
            return {
                "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
                "user_id": UUID(record["user_id"])
                if isinstance(record["user_id"], str)
                else record["user_id"],
                "deleted_at": record.get("deleted_at"),
            }

        except Exception as exc:
            logger.exception(
                "Failed to fetch meal: %s for user: %s",
                meal_id,
                user_id,
            )
            raise RuntimeError(f"Failed to fetch meal: {exc}") from exc

    async def get_active_run(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Check if there's an active (queued or running) analysis run for a meal.

        Args:
            meal_id: Meal identifier
            user_id: User identifier for authorization

        Returns:
            Active analysis run record dict, or None if no active run exists

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .select("id,meal_id,status,run_no")
                .eq("meal_id", str(meal_id))
                .eq("user_id", str(user_id))
                .in_("status", ["queued", "running"])
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                return None

            record = response.data[0]
            return {
                "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
                "meal_id": UUID(record["meal_id"])
                if isinstance(record["meal_id"], str)
                else record["meal_id"],
                "status": record["status"],
                "run_no": record["run_no"],
            }

        except Exception as exc:
            logger.exception(
                "Failed to check active runs for meal: %s user: %s",
                meal_id,
                user_id,
            )
            raise RuntimeError(f"Failed to check active runs: {exc}") from exc

    async def get_next_run_no(
        self,
        *,
        meal_id: UUID | None,
        user_id: UUID,
    ) -> int:
        """Determine the next run_no for a meal or ad-hoc analysis.

        Args:
            meal_id: Meal identifier (None for ad-hoc text analysis)
            user_id: User identifier for authorization

        Returns:
            Next sequential run number (1 if no previous runs exist)

        Raises:
            RuntimeError: If database query fails
        """
        try:
            # For ad-hoc analysis (meal_id is None), always return 1
            # Each ad-hoc analysis is treated as independent
            if meal_id is None:
                return 1

            # Get max run_no for this meal
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .select("run_no")
                .eq("meal_id", str(meal_id))
                .eq("user_id", str(user_id))
                .order("run_no", desc=True)
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                return 1

            max_run_no = response.data[0]["run_no"]
            return max_run_no + 1

        except Exception as exc:
            logger.exception(
                "Failed to get next run_no for meal: %s user: %s",
                meal_id,
                user_id,
            )
            raise RuntimeError(f"Failed to get next run_no: {exc}") from exc

    async def insert_run(
        self,
        *,
        user_id: UUID,
        meal_id: UUID | None,
        run_no: int,
        status: str,
        model: str,
        threshold_used: Decimal,
        raw_input: dict[str, Any],
        retry_of_run_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Insert a new analysis run record.

        Args:
            user_id: User identifier
            meal_id: Meal identifier (None for text-based analysis runs)
            run_no: Sequential run number
            status: Initial status (typically 'queued')
            model: AI model identifier
            threshold_used: Confidence threshold
            raw_input: Raw input data passed to the model
            retry_of_run_id: Optional previous run being retried

        Returns:
            Created analysis run record dict

        Raises:
            RuntimeError: If database insert fails
        """
        try:
            payload = {
                "user_id": str(user_id),
                "meal_id": str(meal_id) if meal_id is not None else None,
                "run_no": run_no,
                "status": status,
                "model": model,
                "threshold_used": float(threshold_used),
                "raw_input": raw_input,
            }

            if retry_of_run_id is not None:
                payload["retry_of_run_id"] = str(retry_of_run_id)

            response = self._client.table(self._ANALYSIS_RUNS_TABLE).insert(payload).execute()

            if not response.data or len(response.data) == 0:
                raise RuntimeError("Insert returned no data")

            record = response.data[0]
            return self._normalize_queued_run_record(record)

        except Exception as exc:
            logger.exception(
                "Failed to insert analysis run for meal: %s user: %s",
                meal_id,
                user_id,
            )
            raise RuntimeError(f"Failed to insert analysis run: {exc}") from exc

    async def update_status(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update the status of an analysis run.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization
            status: New status value
            error_code: Optional error code (for failed status)
            error_message: Optional error message (for failed status)

        Raises:
            RuntimeError: If database update fails
        """
        try:
            payload: dict[str, Any] = {"status": status}

            if error_code is not None:
                payload["error_code"] = error_code
            if error_message is not None:
                payload["error_message"] = error_message

            if status in ("succeeded", "failed", "cancelled"):
                payload["completed_at"] = datetime.utcnow().isoformat()

            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .update(payload)
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.warning(
                    "Update status affected 0 rows",
                    extra={"run_id": str(run_id), "user_id": str(user_id)},
                )

        except Exception as exc:
            logger.exception(
                "Failed to update status for run: %s user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to update status: {exc}") from exc

    async def complete_run(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        status: str,
        latency_ms: int,
        tokens: int,
        cost_minor_units: int,
        cost_currency: str,
        raw_output: dict[str, Any],
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """Complete an analysis run with final status and metrics.

        Updates run with processing results: status (succeeded/failed),
        performance metrics (latency, tokens, cost), and raw AI output.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization
            status: Final status ('succeeded' or 'failed')
            latency_ms: Processing time in milliseconds
            tokens: Number of tokens consumed
            cost_minor_units: Cost in minor currency units (e.g., cents)
            cost_currency: Currency code (e.g., 'USD')
            raw_output: Raw AI model output (JSON)
            error_code: Optional error code (for failed status)
            error_message: Optional error message (for failed status)

        Returns:
            Updated run record with all fields

        Raises:
            RuntimeError: If database update fails
        """
        from postgrest.exceptions import APIError

        try:
            # Prepare update payload
            payload: dict[str, Any] = {
                "status": status,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "cost_minor_units": cost_minor_units,
                "cost_currency": cost_currency,
                "raw_output": raw_output,
                "completed_at": datetime.utcnow().isoformat(),
            }

            if error_code is not None:
                payload["error_code"] = error_code
            if error_message is not None:
                payload["error_message"] = error_message

            # Update the record
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .update(payload)
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise RuntimeError(f"Run {run_id} not found or update failed")

            # Fetch the complete updated record
            return await self.get_by_id(run_id=run_id, user_id=user_id)

        except APIError as exc:
            logger.error(
                "Supabase API error completing analysis run: %s",
                exc,
                exc_info=True,
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            raise RuntimeError("Database update failed") from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error completing analysis run: %s user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to complete run: {exc}") from exc

    async def cancel_run_if_active(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Cancel an analysis run if it is not in a terminal state.

        Updates the status to 'cancelled' with error_code='USER_CANCELLED'
        only if the current status is 'queued' or 'running'.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization

        Returns:
            Updated run record if cancellation succeeded, None if run was
            already in a terminal state (succeeded/failed/cancelled) or not found

        Raises:
            RuntimeError: If database update fails
        """
        from postgrest.exceptions import APIError

        try:
            # Prepare update payload
            payload: dict[str, Any] = {
                "status": "cancelled",
                "error_code": "USER_CANCELLED",
                "completed_at": datetime.utcnow().isoformat(),
            }

            # Update only if status is NOT in terminal states
            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .update(payload)
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .not_.in_("status", ["succeeded", "failed", "cancelled"])
                .execute()
            )

            # If no rows affected, run was already terminal or not found
            if not response.data or len(response.data) == 0:
                return None

            # Fetch and return the updated record
            return await self.get_by_id(run_id=run_id, user_id=user_id)

        except APIError as exc:
            logger.error(
                "Supabase API error cancelling analysis run: %s",
                exc,
                exc_info=True,
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            raise RuntimeError("Database update failed") from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error cancelling analysis run: %s user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to cancel run: {exc}") from exc

    async def replace_output(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        raw_output: dict[str, Any],
        latency_ms: int,
        tokens: int,
        cost_minor_units: int,
        cost_currency: str = "USD",
    ) -> None:
        """Update analysis run with output data and metrics.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization
            raw_output: Raw output from the AI model
            latency_ms: Processing time in milliseconds
            tokens: Total tokens consumed
            cost_minor_units: Cost in minor currency units
            cost_currency: Currency code (default USD)

        Raises:
            RuntimeError: If database update fails
        """
        try:
            payload = {
                "raw_output": raw_output,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "cost_minor_units": cost_minor_units,
                "cost_currency": cost_currency,
            }

            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .update(payload)
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.warning(
                    "Replace output affected 0 rows",
                    extra={"run_id": str(run_id), "user_id": str(user_id)},
                )

        except Exception as exc:
            logger.exception(
                "Failed to replace output for run: %s user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to replace output: {exc}") from exc

    async def update_meal_id(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        meal_id: UUID,
    ) -> dict[str, Any]:
        """Update analysis run with meal_id after meal creation.

        Used for text-based analysis runs where meal is created after analysis completes.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization
            meal_id: Meal identifier to link to the run

        Returns:
            Updated analysis run record

        Raises:
            RuntimeError: If database update fails
        """
        from postgrest.exceptions import APIError

        try:
            payload = {"meal_id": str(meal_id)}

            response = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .update(payload)
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise RuntimeError(f"Run {run_id} not found or update failed")

            # Fetch the complete updated record
            return await self.get_by_id(run_id=run_id, user_id=user_id)

        except APIError as exc:
            logger.error(
                "Supabase API error updating analysis run meal_id: %s",
                exc,
                exc_info=True,
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            raise RuntimeError("Database update failed") from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error updating analysis run meal_id: %s user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to update meal_id: {exc}") from exc

    @staticmethod
    def _normalize_queued_run_record(record: dict[str, Any]) -> dict[str, Any]:
        """Normalize queued analysis run record with proper type conversions.

        Args:
            record: Raw database record from insert

        Returns:
            Normalized dictionary with Python types (UUID, datetime, Decimal)

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "run_no", "status", "model", "created_at"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Queued run record missing required fields: {missing}")

        # Parse datetime
        created_at = record["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "meal_id": (
                UUID(record["meal_id"])
                if record.get("meal_id") and isinstance(record["meal_id"], str)
                else record.get("meal_id")
            ),
            "run_no": record["run_no"],
            "status": record["status"],
            "threshold_used": (
                Decimal(str(record["threshold_used"]))
                if record.get("threshold_used") is not None
                else None
            ),
            "model": record["model"],
            "retry_of_run_id": (
                UUID(record["retry_of_run_id"]) if record.get("retry_of_run_id") else None
            ),
            "latency_ms": record.get("latency_ms"),
            "created_at": created_at,
        }

    async def list_runs(
        self,
        *,
        user_id: UUID,
        meal_id: UUID | None = None,
        status: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        sort_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """List analysis runs for a user with optional filters and cursor pagination.

        Args:
            user_id: User identifier for filtering
            meal_id: Optional meal filter
            status: Optional status filter
            created_from: Optional start of date range
            created_to: Optional end of date range
            limit: Maximum number of records to return (should be page_size + 1)
            cursor_created_at: Cursor timestamp for pagination
            cursor_id: Cursor UUID for tie-breaking
            sort_desc: If True, sort by created_at DESC (default), else ASC

        Returns:
            List of analysis run summary dicts

        Raises:
            RuntimeError: If database query fails
        """
        # Columns for summary view
        summary_columns = (
            "id",
            "meal_id",
            "run_no",
            "status",
            "threshold_used",
            "model",
            "created_at",
            "completed_at",
        )

        try:
            # Build base query
            query = (
                self._client.table(self._ANALYSIS_RUNS_TABLE)
                .select(",".join(summary_columns))
                .eq("user_id", str(user_id))
            )

            # Apply filters
            if meal_id is not None:
                query = query.eq("meal_id", str(meal_id))

            if status is not None:
                query = query.eq("status", status)

            if created_from is not None:
                query = query.gte("created_at", created_from.isoformat())

            if created_to is not None:
                query = query.lte("created_at", created_to.isoformat())

            # Apply cursor pagination
            if cursor_created_at is not None and cursor_id is not None:
                # For descending: WHERE (created_at, id) < (cursor_created_at, cursor_id)
                # For ascending: WHERE (created_at, id) > (cursor_created_at, cursor_id)
                # Supabase doesn't support tuple comparisons, so we need to use OR logic
                if sort_desc:
                    # created_at < cursor OR (created_at = cursor AND id < cursor_id)
                    query = query.or_(
                        f"created_at.lt.{cursor_created_at.isoformat()},"
                        f"and(created_at.eq.{cursor_created_at.isoformat()},id.lt.{str(cursor_id)})"
                    )
                else:
                    # created_at > cursor OR (created_at = cursor AND id > cursor_id)
                    query = query.or_(
                        f"created_at.gt.{cursor_created_at.isoformat()},"
                        f"and(created_at.eq.{cursor_created_at.isoformat()},id.gt.{str(cursor_id)})"
                    )

            # Apply sorting and limit
            sort_column = "created_at"
            query = (
                query.order(sort_column, desc=sort_desc).order("id", desc=sort_desc).limit(limit)
            )

            # Execute query
            response = query.execute()

            if not response.data:
                logger.debug(
                    "No analysis runs found for query",
                    extra={
                        "user_id": str(user_id),
                        "meal_id": str(meal_id) if meal_id else None,
                        "status": status,
                    },
                )
                return []

            # Normalize all records
            return [self._normalize_summary_record(record) for record in response.data]

        except Exception as exc:
            logger.exception(
                "Failed to list analysis runs",
                extra={
                    "user_id": str(user_id),
                    "meal_id": str(meal_id) if meal_id else None,
                    "status": status,
                },
            )
            raise RuntimeError("Database query failed") from exc

    def _normalize_summary_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize summary record from Supabase to typed dict.

        Args:
            record: Raw record from Supabase

        Returns:
            Normalized dict with proper Python types

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "run_no", "status", "model", "created_at"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Summary run record missing required fields: {missing}")

        # Parse datetimes
        created_at = record["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        completed_at = record.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "meal_id": (
                UUID(record["meal_id"])
                if record.get("meal_id") and isinstance(record["meal_id"], str)
                else record.get("meal_id")
            ),
            "run_no": record["run_no"],
            "status": record["status"],
            "threshold_used": (
                Decimal(str(record["threshold_used"]))
                if record.get("threshold_used") is not None
                else None
            ),
            "model": record["model"],
            "created_at": created_at,
            "completed_at": completed_at,
        }
