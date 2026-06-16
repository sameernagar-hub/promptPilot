# Phase 10: Open Domain Detection and Confirmation

## Goal

Replace the fixed starter-domain classifier with open domain detection and explicit user confirmation.

## Status

Not started.

## Classification Shape

```txt
primary_domain
subdomain
intent
risk_level
confidence
evidence
alternative_domains
needs_domain_confirmation
confirmed_domain
domain_source: detected | user_confirmed | user_corrected
```

## UX Flow

```txt
detect domain
-> ask "I think this is about X. Is that right?"
-> if yes, continue
-> if no, let user provide or select the correct domain
-> generate domain-aware clarifying questions
```

## Planned Work

- Extend classification schemas and persistence.
- Keep the existing deterministic classifier as a fallback.
- Add an open-domain classifier service that can return alternatives and evidence.
- Add domain confirmation and correction APIs.
- Update prompt generation to use confirmed domains.
- Add UI for confirm, correct, and continue.

## Verification

- [ ] Prompts outside the original four MVP domains can be classified.
- [ ] Ambiguous or low-confidence domains trigger confirmation.
- [ ] User-corrected domains are stored.
- [ ] Confirmed domains drive clarifying questions and generated prompts.
- [ ] Profile analysis can identify recurring user domains.
