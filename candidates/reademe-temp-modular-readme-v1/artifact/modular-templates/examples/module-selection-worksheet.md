# README Module Selection Worksheet

Complete this before assembly. Recording why a module is included or omitted makes the final README easier to review and maintain.

## Project context

| Prompt | Decision |
| --- | --- |
| Primary audience | {{PRIMARY_AUDIENCE}} |
| Project type | {{LIBRARY_CLI_APPLICATION_SERVICE_OR_OTHER}} |
| First reader success | {{FIRST_SUCCESSFUL_OUTCOME}} |
| Canonical docs location | {{DOCS_LOCATION}} |
| Distribution model | {{PUBLIC_INTERNAL_PACKAGE_OR_OTHER}} |
| Supported platforms | {{SUPPORTED_PLATFORMS}} |

## Selection

Use `Yes`, `No`, or `N/A` and record the evidence behind the choice.

| Module | Select | Reason or canonical source |
| --- | --- | --- |
| Project title | Yes | {{CANONICAL_NAME_SOURCE}} |
| Repository alias | {{DECISION}} | {{REASON}} |
| Banner or logo | {{DECISION}} | {{ASSET_OR_REASON}} |
| Badges | {{DECISION}} | {{STATUS_SOURCES_OR_REASON}} |
| Short description | Yes | {{METADATA_SOURCE}} |
| Long description | {{DECISION}} | {{REASON}} |
| Table of contents | {{DECISION}} | {{LENGTH_OR_NAVIGATION_REASON}} |
| Key features | {{DECISION}} | {{CAPABILITY_SOURCE}} |
| Visual demo | {{DECISION}} | {{ASSET_OR_REASON}} |
| Architecture overview | {{DECISION}} | {{ARCHITECTURE_SOURCE_OR_REASON}} |
| Prerequisites | {{DECISION}} | {{MANIFEST_OR_CI_SOURCE}} |
| Installation | {{DECISION}} | {{SUPPORTED_INSTALL_SOURCE}} |
| Configuration | {{DECISION}} | {{SCHEMA_OR_EXAMPLE_SOURCE}} |
| Usage / quickstart | Yes | {{VERIFIED_EXAMPLE_SOURCE}} |
| CLI reference | {{DECISION}} | {{CLI_HELP_SOURCE_OR_REASON}} |
| API reference | {{DECISION}} | {{PUBLIC_API_SOURCE_OR_REASON}} |
| Troubleshooting | {{DECISION}} | {{OBSERVED_FAILURE_SOURCE_OR_REASON}} |
| Security | {{DECISION}} | {{SECURITY_POLICY_SOURCE_OR_REASON}} |
| Maintainers | {{DECISION}} | {{GOVERNANCE_SOURCE_OR_REASON}} |
| Contributing | {{DECISION}} | {{CONTRIBUTION_POLICY_SOURCE_OR_REASON}} |
| Code of conduct | {{DECISION}} | {{CONDUCT_POLICY_SOURCE_OR_REASON}} |
| Acknowledgments | {{DECISION}} | {{ATTRIBUTION_SOURCE_OR_REASON}} |
| Agent instructions pointer | {{DECISION}} | {{AGENTS_FILE_OR_REASON}} |
| LLM index pointer | {{DECISION}} | {{LLMS_INDEX_OR_REASON}} |
| License | {{DECISION}} | {{AUTHORITATIVE_LICENSE_SOURCE}} |

## Ordering decision

- [ ] Use installation before usage for procedural onboarding.
- [ ] Use a short usage preview before installation for rapid interface evaluation.
- [ ] Record any other intentional departure from the default order: {{ORDERING_RATIONALE}}.

## Verification owners

| Concern | Owner | Evidence |
| --- | --- | --- |
| Commands and code examples | {{OWNER}} | {{CI_JOB_OR_MANUAL_TEST}} |
| Public API and CLI surface | {{OWNER}} | {{REFERENCE_SOURCE}} |
| Security and governance routes | {{OWNER}} | {{POLICY_REVIEW}} |
| License and notices | {{OWNER}} | {{LEGAL_SOURCE}} |
| Rendered links and media | {{OWNER}} | {{LINK_CHECK_OR_PREVIEW}} |
