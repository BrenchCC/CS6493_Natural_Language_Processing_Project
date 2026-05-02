import time
import logging
import threading
from collections import deque
from typing import Optional, Tuple


class _SlidingWindowRateLimiter:
    def __init__(self, *, rpm: int, tpm: int, window_s: float = 60.0) -> None:
        self._rpm = max(0, int(rpm))
        self._tpm = max(0, int(tpm))
        self._window_s = float(window_s)
        self._lock = threading.Lock()
        self._req_ts: deque[float] = deque()
        self._token_events: deque[Tuple[float, int]] = deque()
        self._token_sum = 0

    def _prune_locked(self, now: float) -> None:
        while self._req_ts and now - self._req_ts[0] >= self._window_s:
            self._req_ts.popleft()
        while self._token_events and now - self._token_events[0][0] >= self._window_s:
            _, tok = self._token_events.popleft()
            self._token_sum -= tok

    def acquire(self, *, reserve_tokens: int) -> None:
        reserve_tokens = max(0, int(reserve_tokens))
        if self._rpm <= 0 and self._tpm <= 0:
            return

        while True:
            now = time.monotonic()
            with self._lock:
                self._prune_locked(now)

                req_wait = 0.0
                if self._rpm > 0 and len(self._req_ts) >= self._rpm:
                    req_wait = self._window_s - (now - self._req_ts[0])

                tok_wait = 0.0
                if self._tpm > 0 and self._token_sum + reserve_tokens > self._tpm:
                    need = self._token_sum + reserve_tokens - self._tpm
                    freed = 0
                    for ts, tok in self._token_events:
                        freed += tok
                        if freed >= need:
                            tok_wait = self._window_s - (now - ts)
                            break

                wait_s = max(req_wait, tok_wait, 0.0)
                if wait_s <= 0:
                    self._req_ts.append(now)
                    self._token_events.append((now, reserve_tokens))
                    self._token_sum += reserve_tokens
                    return

            time.sleep(max(0.01, wait_s))

    def add_tokens_after_request(self, tokens: int) -> None:
        tokens = int(tokens)
        if tokens <= 0 or self._tpm <= 0:
            return
        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)
            self._token_events.append((now, tokens))
            self._token_sum += tokens

    @staticmethod
    def estimate_tokens_text(text: str) -> int:
        """Rough token estimate for throttling.

        Args:
            text (str): Input text.

        Returns:
            int: Estimated tokens.
        """
        text = str(text or "").strip()
        if not text:
            return 0
        ascii_count = 0
        for ch in text:
            if ord(ch) < 128:
                ascii_count += 1
        non_ascii = len(text) - ascii_count
        return max(1, int(ascii_count / 4 + non_ascii / 1.5))

    @staticmethod
    def format_duration_s(seconds: float) -> str:
        """Format seconds as H:MM:SS / M:SS.

        Args:
            seconds (float): Elapsed seconds.

        Returns:
            str: Formatted duration.
        """
        seconds = max(0, int(seconds))
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

    @staticmethod
    def print_progress(
        *,
        processed: int,
        total: int,
        error_count: int,
        start_ts: float,
        logger: Optional[logging.Logger] = None,
        flush: bool = False,
    ) -> None:
        """Print progress line to stdout or logger.

        Args:
            processed (int): Processed items.
            total (int): Total items.
            error_count (int): Error count.
            start_ts (float): Start monotonic ts.
            logger (logging.Logger | None): If provided, log via logger.info; otherwise print.
            flush (bool): Only for print mode.
        """
        now = time.monotonic()
        elapsed = max(1e-6, now - start_ts)
        rpm = processed / elapsed * 60.0
        remaining = max(0, total - processed)
        eta_s = remaining / max(1e-9, processed / elapsed) if processed > 0 else 0.0
        pct = (processed / total * 100.0) if total else 100.0
        msg = (
            f"Processed {processed}/{total} ({pct:.1f}%), "
            f"errors={error_count}, "
            f"speed={rpm:.2f} req/min, "
            f"elapsed={_SlidingWindowRateLimiter.format_duration_s(elapsed)}, "
            f"eta={_SlidingWindowRateLimiter.format_duration_s(eta_s)}"
        )
        if logger is not None:
            logger.info(msg)
            return
        print(msg, flush = bool(flush))