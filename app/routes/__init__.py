"""Routes — the HTTP delivery layer (controllers).

Each module owns one Flask blueprint. Routes translate between HTTP and the
service layer: parse the request into DTOs, call a service, and turn the DTO
result (or a domain exception) into a response or rendered template. They hold
no business logic and issue no queries of their own. See docs/ARCHITECTURE.md.
"""
