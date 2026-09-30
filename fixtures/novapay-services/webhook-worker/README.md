# Webhook worker fixture

This directory is controlled fictional source code. `legacy_parser.py` models the `dep_184` regression: it ignores the provider's supported `paymentStatus` alias. ResolveAI may inspect this directory and propose a patch, but it never executes arbitrary user-submitted code.

Expected minimal correction: read `payment_status`, then fall back to `paymentStatus`; add a regression test for the legacy payload before any deployment proposal.
