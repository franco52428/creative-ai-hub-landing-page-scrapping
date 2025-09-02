---
applyTo: '**'
---

## Architectural Principles (Hexagonal & DDD)

* **Hexagonal Architecture:** Organize code into distinct layers (Domain, Application, Infrastructure, Interfaces) following a ports-and-adapters style. Business logic resides in the core (Domain/Application) and is **isolated** from technical details (Infrastructure/Interfaces).
* **Domain-Driven Design Boundaries:** Maintain clear boundaries between:

  * **Domain Layer:** Pure business logic (entities, value objects, domain events, repository **interfaces**).
  * **Application Layer:** Application logic (use cases, services, DTOs) that orchestrates domain operations and interactions with ports.
  * **Infrastructure Layer:** Technical details (database implementations, external API clients/adapters) fulfilling the contracts defined by domain or needed by application.
  * **Interfaces Layer:** User-facing or external interface code (e.g. Flask controllers, CLI, etc.) handling input/output.
* **Layer Independence:** Each layer should depend only on the layers **inside** it (e.g. Application can depend on Domain, but Domain must not depend on Application; Infrastructure should depend on Domain interfaces, not vice versa). This ensures high **modularity** and low coupling.
* **Conform to Existing Structure:** When adding code, **do not introduce new architectural patterns or layers**. Fit the code into the existing Hexagonal structure. Do not bypass or ignore these layers (e.g. no direct DB calls in controllers, no business logic in infrastructure).
* **High Cohesion & Low Coupling:** Keep related logic together and unrelated logic separated. Each class or module should have a single clear purpose. Cross-layer interactions should happen via well-defined interfaces or DTOs, not by reaching into another layer's internals.
* **Testability & Clean Code:** Design modules so they can be unit-tested in isolation (use dependency injection and interfaces to decouple). Follow clean code practices: meaningful naming, small functions, clear control flow, and comprehensive documentation for complex parts.

## Domain Layer Guidelines

* **Entities as Core Business Models:** Define domain entities (usually as `@dataclass` classes) in `app/domain/entities/**`. These represent core business data and rules. They may include domain-specific methods (e.g. `mark_email_verified()` on a User entity) but should avoid any external system calls or side effects.
* **Value Objects & Types:** Encapsulate concept values (if any) within the domain. Keep domain classes focused on business state and invariants.
* **Domain Events:** For significant business occurrences, use domain events. Domain events (e.g. `MessageCompletedEvent`) are defined under domain (e.g. `app/domain/entities/.../events`). They should subclass a base `DomainEvent` and carry relevant info. Use the `EventDispatcher` (in domain) to publish these events. **Do not** call external services directly from domain entities; instead, raise an event and let other layers react.
* **Repository Interfaces:** Define abstract repository classes in `app/domain/repositories/**` for each aggregate or entity that needs persistence. These should subclass `ABC` and declare methods like `create`, `update`, `find_by_id`, etc., without implementation. For example, `UserRepository` in domain defines what operations are needed for User persistence. **Do not implement database logic here** – just the interface.
* **No Framework or Tech Dependencies:** The domain layer must remain framework-agnostic. **Do not import** Flask, database drivers, or Celery in domain code. The domain should not be aware of HTTP requests, JSON, or persistence mechanisms. It deals with pure business concepts.
* **Use Domain Exceptions:** On detecting business rule violations or missing data, domain logic can raise custom exceptions (e.g. `ValidationException`, `NotFoundException`) defined under `app/utils/exceptions`. This signals error conditions to the application layer in a controlled way. Do not use HTTP responses or exit calls in domain logic.
* **Consistency and Clarity:** Name domain classes and interfaces clearly after business concepts (e.g. `Assistant`, `Lead`, `Message`, `UserRepository`, etc.). Keep their responsibilities narrow. All domain code should be easily understandable without knowledge of how data is stored or how requests come in.

## Application Layer Guidelines

* **Purpose:** The application layer (often called **use cases** or **services**) coordinates domain activities to fulfill application actions. It lives under `app/application/**` and is the main point of entry for both the Interfaces layer (synchronous calls) and Celery tasks (asynchronous calls).
* **Use Case Classes:** Implement each high-level operation or user story as a use case class in `app/application/use_cases/**`. For example, `AssistantTypeUseCase`, `LeadUseCase`, `RegisterUserUseCase`. These classes orchestrate calls to domain repositories, domain entities, and application services to execute a complete action.

  * **Use Case Design:** Inject all required dependencies into the use case’s constructor (via the AppContainer). A use case may need one or multiple services, repository interfaces, or adapters to do its job. This injection makes testing easier and keeps the use case decoupled from specific implementations.
  * **Use Case Methods:** Expose clear methods (e.g. `create_assistant_type(dto)` or `execute()` for generic flows) that the interface layer or tasks will call. Inside these methods, perform input validation (e.g. ensure required DTO or IDs are provided), call the appropriate service methods or domain operations, handle exceptions, and return a result (usually a domain entity or simple data).
  * **No Heavy Logic in Controllers/Tasks:** **All** significant business decisions and sequencing should be in use cases or services, not in the Flask controllers or Celery tasks. The interface layer should ideally just call a use case.
* **Service Classes:** The application layer also contains service classes in `app/application/services/**` that encapsulate logic for a specific domain entity or subset of functionality (e.g. `AssistantService`, `LeadService`, `OTPService`). These often wrap repository calls and enforce business rules that involve that entity:

  * **Service Responsibilities:** Provide methods for create/update/delete/fetch operations and any entity-specific logic (e.g. checking for duplicates, applying business validations). Services often directly use domain repository interfaces and may utilize multiple repositories if needed (e.g. `AssistantService` uses `AssistantRepository` and `AssistantTypeRepository` to ensure consistency).
  * **Use Domain Models:** Service methods should construct domain entity instances (using domain classes) from DTOs or input data, then call repository methods to persist. They also handle conversion from domain objects to DTOs if needed (though often use cases or controllers handle final formatting).
  * **Exception Handling:** Catch and rethrow exceptions as needed to maintain abstraction. For instance, if a repository raises a low-level error (like a `MongoException`), the service can catch it, log it, and raise a higher-level exception or a generic `RuntimeError` to signify failure without exposing details to the domain logic. Services should also raise `ValidationException` or `NotFoundException` when business conditions are not met (e.g. trying to update a non-existent resource).
* **DTO (Data Transfer Objects):** Use **DTO classes** for moving data in/out of the application layer:

  * Define DTOs in `app/application/dtos/**` (grouped by domain entity or feature). For example, `AssistantTypeCreateDTO`, `MessageUpdateDTO`, etc. These are typically `@dataclass`es or Pydantic models that specify the structure of input or output data.
  * **Why DTOs:** They ensure that only the required data is passed between layers (e.g. from controller to use case, or from use case to task) and provide validation and defaults. **Always use or extend an existing DTO** rather than passing raw dictionaries or request objects into the use case. If new data is needed, extend the DTO or create a new one.
  * Each DTO should have classmethods like `from_dict` (as seen in the code) to facilitate creation from a dict (e.g. from request JSON) and make conversion easy. This keeps parsing logic out of the core flow.
* **No External Calls:** Application layer should not make direct calls to databases or external APIs. It should always go through domain **interfaces** (repositories) or use infrastructure **adapters** provided via dependency injection. For example, if you need to send an email in a use case, call an EmailAdapter (injected via container) instead of using an SMTP library here.
* **Boundary Enforcement:** The application layer is a consumer of domain and provider to infrastructure:

  * It **consumes domain** by using entities and repository interfaces (the domain is the inner circle).
  * It **calls into infrastructure** only via *ports/adapters* exposed to it (like a repository implementation or an external service client, provided by container).
  * **Never import** concrete infrastructure classes in application code. Instead, accept them through constructors (e.g. the container injects an `OpenAIClient` instance or a `MongoRepository` instance as needed).
* **Logging in Application:** Use logging to record significant events in use cases and services (`logger = logging.getLogger("<name>")`). Include context (like correlation IDs, entity IDs, etc.) using `extra` so that logs are traceable. For instance, log success or failure of an operation with identifiers. **Do not log sensitive information** (like passwords or full personal data).
* **Maintain Readability:** Keep use case and service methods concise and focused. If a method is doing too much, consider splitting it or moving some logic into the domain (if purely business logic) or into a helper. Use clear naming (e.g. `create_assistant`, `send_otp`) and docstrings to describe complex behaviors. This layer’s code should narrate the “application story” clearly.

## Context Strategies (Application Layer)

* **Message Context Strategies:** Context strategies are implemented in `app/application/services/message/context_strategies/` and follow the Strategy pattern for extracting different types of context from messages.

### Available Strategies

* **LastReasonContextStrategy:** Extracts the `reason` field from the last `SetterSteps` in a message, formatting it with the assistant's name:
  * **Input:** Message with setter_steps containing openai_response with reason field
  * **Output:** `<ASSISTANT_NAME>:\n{"reason": <REASON>}\n`
  * **Usage:** Factory identifier: `"LAST_REASON"`
  * **Error Handling:** Returns empty string if no setter_steps, reason, or required data is missing
  * **Robustness:** Supports multiple openai_response formats (dict, object attributes, __getitem__)

* **LastResponseContextStrategy:** Extracts the last response from a message
* **LastMessageContextStrategy:** Extracts the last message content
* **AllMessagesContextStrategy:** Aggregates all messages in context
* **CompositeContextStrategy:** Combines multiple strategies in ordered execution

### Strategy Implementation Guidelines

* **Inheritance:** All strategies must inherit from `MessageContextStrategy` base class
* **Single Responsibility:** Each strategy focuses on one specific type of context extraction
* **Consistent Output:** Follow established JSON formatting patterns for structured data
* **Error Handling:** Gracefully handle missing data by returning empty strings
* **Factory Registration:** Register new strategies in `MessageContextFactory.get_strategy()`
* **Testing:** Comprehensive unit tests required for all extraction scenarios and edge cases

### Integration Patterns

* **Factory Pattern:** Use `MessageContextFactory` for strategy creation and management
* **Composite Pattern:** Multiple strategies can be combined using `CompositeContextStrategy`
* **Dependency Injection:** Factory receives `MessageService` for complex operations
* **Type Safety:** Use proper type hints and domain entities for robust integration

## Infrastructure Layer Guidelines

* **Role:** The infrastructure layer provides concrete implementations for the ports needed by the application/domain. It includes database repositories, external API clients, messaging adapters, etc., all under `app/infrastructure/**`.
* **Repository Implementations:** For each domain repository interface, provide an implementation in `app/infrastructure/repositories/**`:

  * Use a naming convention that indicates the technology, e.g. `MongoUserRepository` implements `UserRepository` for MongoDB.
  * In the repository `__init__`, obtain the database connection from the centralized `Database` utility (e.g. `db = Database.get_db()`), and select the relevant collection. **Do not** create new DB connections spontaneously; rely on the configured `Database` (which is initialized in the container with app config).
  * Implement all abstract methods from the domain interface (create, update, find, etc.). These methods should translate domain entities to the database format (e.g. converting a `User` object to a dict of fields for Mongo) and vice versa.
  * Handle database exceptions (e.g. `PyMongoError` or similar) by logging an error and raising a `MongoException` or general exception. This prevents low-level exceptions from leaking upward. If an operation fails (like duplicate key), raise a meaningful exception or return None as appropriate, and let the service/use case layer decide how to handle that result.
  * Ensure repository methods **return domain entities or domain types**. For example, `find_by_id` should return an instance of `User` or `None`. Reconstruct the domain object using either the domain constructor or a helper method (many repos have an internal `_doc_to_entity` for this purpose). Keep the mapping logic within the repository.
  * Do not impose business logic in repository (e.g. don’t decide *which* user to create or validate business rules here – that belongs in application layer). The repo simply executes data operations and minimal data integrity checks (like preventing duplicates if required by design).
* **External Adapters/Clients:** For integration with external services (OpenAI, email/SMS services, third-party APIs, etc.), implement adapters in `app/infrastructure/adapters/**`:

  * Adapters encapsulate all the details of calling the external system (endpoints, authentication, request/response format). E.g. `OpenAIClient` handles making requests to OpenAI API, `ManyChatAdapter` interacts with ManyChat API, `EmailAdapter` sends emails via some service.
  * Accept configuration (API keys, URLs) via the constructor or via dependency injection (the AppContainer will supply these from config). Do not hard-code credentials or URLs.
  * Provide clear methods that the application layer can call (e.g. `send_message(to, content)` for an SMS adapter). These methods should hide the HTTP requests or library calls and just expose a simple interface.
  * Use **pydantic models or DTOs** if complex data is passed to/from the external service (as seen in `app/infrastructure/adapters/open_ai/dto/**`). This keeps external data handling organized.
  * Log interactions and errors at the adapter level. Use `logger` to record calls to external services (maybe at debug/info level) and warn/error when something fails, including enough context (but avoid sensitive data).
  * Adapters can be considered **secondary ports** in Hexagonal architecture. They should be invoked by application services or use cases, not by domain.
* **Infrastructure Utilities:** If there are other technical utilities (e.g. a custom logging handler writing to Mongo, etc.), implement them under infrastructure or utils as appropriate. For example, if there's a `MongoDBHandler` for logging (as seen in code), it belongs in infrastructure.
* **No Upward Dependencies:** The infrastructure layer **must not** depend on the application or interfaces layers. It can depend on domain (for entity classes or interface definitions) and on `app/utils` for common utilities. Infrastructure is the outer layer, so it should not import from `app/application` or `app/interfaces`.
* **Consistency in Implementation:** Follow patterns of existing infrastructure code. For instance, if all repository classes follow a pattern (initialize collection, use `_doc_to_entity`, etc.), new repositories should mimic that structure. If using Celery or other tools in infrastructure, ensure it aligns with how the project expects (though generally Celery tasks are under a separate `app/task` module).
* **Security & Error Handling:** Never trust external input: validate or sanitize data coming from external systems in the adapter if necessary, or at least pass it through the application layer for validation. Wrap external errors in project-specific exceptions to give meaningful context to the upper layers. For example, catch an HTTP error from an API and raise an `OpenAIClientException` with a user-friendly message if appropriate.
* **Logging Database Ops:** Especially for critical ops (create/update/delete), log successes and failures with context (IDs, counts) using the logger (as seen with messages like "✅ Usuario creado con éxito" in repositories). Use these logs to aid debugging, but ensure they don't overflow (logging every trivial read might not be needed unless helpful).
* **Side-Effect Delegation:** If an infrastructure component needs to trigger further actions (e.g. an event handler that calls an adapter), consider whether it should be done in a synchronous call or via a Celery task. For example, sending an email might be fine directly in an adapter call, but if it's triggered from a domain event, it might be better as a separate step to avoid slowing down the main flow. Align with how existing event handlers and tasks work (see “side-effect delegation” below for more).

## Interfaces Layer Guidelines

* **Purpose:** The interfaces layer is the boundary where external input (HTTP requests, CLI commands, etc.) enters the system and where output is returned. For a web API, this is primarily the Flask controllers and related middleware, located in `app/interfaces/**`.
* **Flask Controllers:** Routes and controllers under `app/interfaces/controllers/**` should:

  * Define Flask routes (Blueprints, endpoints) and methods (GET, POST, etc.) for each API endpoint. Group endpoints logically by context (e.g. `assistant_controller.py` for assistant-related endpoints).
  * Parse incoming data from `flask.request` (query params, JSON body, etc.). **Validate** the presence of required fields (the `validate_json_body` decorator in utils can help, or manual checks).
  * Construct appropriate DTOs or simple parameters to pass to the application layer. Do not pass the raw `request` or unvalidated JSON directly to a use case.
  * Call the appropriate **use case** or **service** via the AppContainer. For example, get an instance: `use_case = current_app.config["container"].assistant_use_case()`, then call `use_case.create_assistant(dto)`. This ensures the controller is thin and delegates the heavy lifting to application logic.
  * **Asynchronous operations:** If an endpoint triggers a long-running process (e.g. generating a complex report, calling OpenAI, etc.), do **not** block the request. Instead, offload to a Celery task:

    * Launch the task by calling `task_xyz.delay(parameters)`.
    * If appropriate, immediately return a response indicating the task has started (202 Accepted, with maybe a task ID or message).
    * Optionally, you can implement a short wait (as seen in some patterns) for quick results, but ensure not to exceed a couple of seconds and handle timeout by returning a 202.
  * Use the `standard_response(success, code, message, data)` utility to format all responses uniformly. This ensures the API always returns a JSON with `status`, `code`, `msg`, and `data`.
  * Map exceptions to HTTP responses:

    * `ValidationException` -> return a 400 Bad Request (with the exception message or a relevant error message).
    * `NotFoundException` -> return a 404 Not Found.
    * Custom exceptions (like `OpenAIClientException`) -> could be 502 Bad Gateway or 500 depending on context, but generally log it and return a 500 with a generic message to avoid leaking details.
    * Generic Exception (unexpected) -> log as error and return 500 Internal Server Error with a generic message.
  * **Never expose stack traces or raw exception messages to the client.** Always handle exceptions and return a controlled message.
* **Request Context & Middleware:** Utilize middleware in `app/interfaces/middleware/**` for cross-cutting concerns:

  * `correlation_middleware`: automatically assigns a unique `X-Correlation-ID` (from header or generated) to each request and stores it in `flask.g.correlation_id`. **Always preserve this correlation ID** in logs and when spawning tasks (you can pass it as a task argument or use logging).
  * `request_logging`: logs each HTTP request (method, path, status, duration, client IP, user agent, and correlation ID) after the response is sent. Don't duplicate this logging in controllers; rely on middleware to capture it.
  * `cors_middleware`: sets CORS headers as configured. Do not implement CORS logic in individual controllers; keep it centralized here.
  * If adding new middleware (authentication, rate limiting, etc.), follow the pattern: define a function that takes the app and uses `@app.before_request` or `@app.after_request` to inject behavior.
* **No Business Logic in Controllers:** Ensure controllers **only** coordinate the request/response, and possibly minor flow control for async tasks. All conditional logic around entities, calculations, and decisions should be done in the application layer. If you find a controller doing complex things, refactor that into a use case.
* **No Direct Data Access:** Controllers must not query the database or call infrastructure directly. They should **never** instantiate a repository or call `Database.get_db()` or run raw queries. Always go through the use case/service which uses the repository. This keeps the interface layer agnostic of how data is stored.
* **Dependency Injection in Controllers:** Access the `AppContainer` via `current_app.config["container"]`. Do not manually create service or use case instances inside controllers; always use the container to respect the configured dependencies (this ensures, for example, you’re using the same repository instance or configuration as the rest of the app).
* **Validation:** While DTOs will handle type validation, the interface layer should ensure required fields are present to avoid passing bad data down. Utilize existing decorators like `@validate_json_body` (which likely checks that the request JSON matches an expected schema or has required keys) to simplify this.
* **Output Structure:** For consistency, the `standard_response` helper should wrap all responses. Even error responses should ideally go through it (some controllers might directly use `jsonify`, but the convention is a unified format). Maintain this standard so clients always receive a uniform response format.
* **Logging in Interface:** Use logging to record high-level events like "Received request to create assistant" and outcomes like "Assistant created successfully" or errors. Include `g.correlation_id` and any important identifiers in these logs via `extra`. This, combined with request\_logging middleware, gives an end-to-end trace.

## Asynchronous Tasks (Celery) Guidelines

* **When to Use Celery:** Use Celery tasks for any operation that is long-running, CPU-intensive, or involves waiting on external services. The project uses Celery extensively for flows involving assistant messages, leads, nodes, threads, etc., to ensure responsive APIs and to offload work.
* **Task Location and Structure:** Define tasks in the `app/task/**` directory, grouping by domain (e.g. `assistant/assistant_celery_task.py`, `message/message_celery_task.py`, etc.). Each task is a function decorated with `@celery.task`. Follow the naming conventions:

  * Use a descriptive `name` for the task in the decorator (e.g. `name="task_create_assistant_type"`). This name is used when calling or scheduling tasks.
  * Set Celery options as per existing patterns: for critical tasks, use `bind=True` and `autoretry_for=(Exception,)` with `max_retries` and `default_retry_delay` to auto-retry on failure. This prevents tasks from silently failing on transient errors.
* **Task Implementation:** Inside the task function:

  * Immediately get a logger for the task (e.g. `logger = logging.getLogger("assistant-type-celery-task")`) if not already at module level, and log the start of the task with context (e.g. input data or IDs).
  * Use the **AppContainer** to retrieve necessary use cases or services. Example: `use_case = current_app.config["container"].assistant_type_use_case()`. This ensures the task uses the same configuration and dependencies as the main app.
  * Convert inputs to DTOs or appropriate domain inputs. For instance, if the task receives a dict of `assistant_type_data`, create a DTO: `dto = AssistantTypeCreateDTO(**assistant_type_data)` before calling the use case.
  * Call the use case or service method to perform the action (e.g. `assistant_type_created = use_case.create_assistant_type(dto)`). The task should not contain complex business logic itself; delegate to the application layer.
  * **Exception Handling in Tasks:** Wrap the call in a try/except:

    * Catch expected exceptions like `ValidationException`, `NotFoundException`, `MongoException`, etc., and handle them gracefully. Usually, for these, you would log a warning or info (since these are business/domain errors, not system errors) and then re-raise the exception to mark the task as failed (or simply allow them to propagate, which Celery will treat as failure without retry if you haven’t added them to `autoretry_for`).
    * Catch broad `Exception` last, log it as an error (with traceback if possible), and if `autoretry_for=(Exception,)` is set, use `raise self.retry(exc=e)` to trigger the auto-retry mechanism. This helps in case of transient issues (e.g. network failures).
  * On successful completion, log an info message indicating success and any relevant output identifiers (like the ID of the created entity). If the task returns a result (to be used by other tasks or the caller), ensure to return serializable data (e.g. use `asdict(domain_object)` to return primitive types or a DTO converted to dict).
* **Task Chaining & Scheduling:** If tasks need to trigger subsequent tasks or operate in sequence:

  * Use `apply_async` with `eta` or countdown for scheduling (as seen with `task_process_message.apply_async(args=[...], eta=some_time)` to schedule future execution).
  * Alternatively, use Celery canvas primitives (chains, chords) if needed, but maintain the code clarity.
  * Do not perform long polling loops or sleeps inside tasks to wait for something; instead schedule another task or requeue the same task with a delay. Keep each task focused.
* **Reusing Patterns:** When creating a new task, mirror the structure of existing tasks:

  * **Naming:** e.g., `task_<action>_<entity>` for the function and `"task_<action>_<entity>"` for the Celery name.
  * **Logging:** consistent format (start, success, error messages with context).
  * **Retries:** similar retry policy if the task is critical (most existing tasks have 5 retries, 5-minute countdown).
  * **Binding (`self` usage):** If you use `bind=True` (to allow self.retry), remember to include `self` in function signature and call `self.retry` on exceptions as needed.
* **Passing Context:** If a task needs certain context from the request (like correlation\_id), pass it as a parameter when calling `.delay()` or `.apply_async`. For example, `task.delay(data, correlation_id=g.correlation_id)`. Then use it in the task for logging. **Never rely on Flask `g` inside a task**, since tasks run outside request context.
* **Celery Best Practices:**

  * Keep tasks **idempotent** when possible (retrying shouldn’t cause adverse effects). If not fully idempotent, handle via checks (e.g. check if something was already done before repeating).
  * Do not make tasks overly large. Break down complex processes into multiple tasks that can be linked, as the project does for message processing (retrieve lead -> create message -> process message in sequence).
  * Free resources in tasks if needed (close any sessions or large objects, though typically not an issue with short tasks).
* **Error Propagation:** Decide what to do with task exceptions. In some flows, the controller waits for the task result (with a timeout) and handles failures. In others, tasks might be fire-and-forget. Ensure your task communicates status appropriately:

  * If the controller is waiting (synchronous wait on result), any exception will propagate to the `.get()` call. In those cases, it’s important to catch known exceptions in the task and perhaps return a special value or raise a controlled exception that the controller can interpret if needed.
  * If no one waits for result (fire-and-forget tasks like sending an email), just ensure to log errors; Celery will handle retries as configured.
* **No Flask in Tasks (except container):** Similar to other layers, tasks should not start manipulating Flask app state. They can use `current_app.config` to get the container or config values, but they shouldn't, for example, try to send HTTP responses or use Flask request data. They operate in the background context only with what was passed in.

## Logging and Exception Handling

* **Structured Logging:** The project uses structured logging with context to make debugging easier:

  * Always create a logger per module or class context: e.g., `logger = logging.getLogger("assistant-service")` or `"lead-celery-task"`. Use a clear, module-specific name (typically `"<component>-<context>"`).
  * **Context via `extra`:** When logging, include contextual data using the `extra` parameter of logger methods. For example, `logger.info("User created", extra={"user_id": user.id, "email": user.email})`. This ensures these fields appear in the log record (especially if logs are output as JSON).
  * Always log the `correlation_id` in contexts related to a request or flow. In a Flask request, retrieve it via `g.correlation_id`. In a Celery task, include it if passed. Example: `extra={"correlation_id": corr_id, ...}`. This way, you can trace a single request or operation across services and tasks.
  * Log at the appropriate level:

    * `logger.debug()`: Very detailed information, typically not enabled in production (use sparingly).
    * `logger.info()`: Normal operational messages (e.g. start and successful end of operations, key steps reached).
    * `logger.warning()`: An indication of something unexpected or a potential problem (e.g. validation failed, missing data) that isn’t fatal.
    * `logger.error()`: An error occurred that prevented an operation from completing. Use this for exceptions caught that are not normal business flow.
    * Avoid using `critical` unless the application is going down or a very severe situation; `error` is usually sufficient for exceptions.
  * **No Sensitive Data:** Do not log passwords, secrets, or personal user data. Mask or omit sensitive fields. Logging should help debug, not expose data.
  * Consistent messaging: Use similar phrasing as existing logs for similar events (e.g. use "successfully created" vs "created successfully" consistently).
* **Exception Hierarchy:** The project defines custom exceptions in `app/utils/exceptions/**`. Always use these in place of generic exceptions for known error cases:

  * `ValidationException`: Use when input data or business rules are violated (e.g. required field missing, format wrong, or a domain-specific rule like "assistant name already exists").
  * `NotFoundException`: Use when an expected entity or record is not found (e.g. looking up a User by ID that doesn't exist).
  * `OpenAIClientException`: Use to wrap errors coming from the OpenAI API client. For example, if the OpenAI API returns an error or times out, raise this exception with a message.
  * `MongoException`: Use to indicate lower-level database errors. A repository might throw this if a MongoDB operation fails unexpectedly.
  * If new categories of errors are needed, extend this exceptions module appropriately. Keep exceptions organized and named by context.
  * **Raising Exceptions:** When raising, provide a clear message. This message might be logged or even returned to the client (for Validation or NotFound). For internal exceptions like `MongoException`, the message can be generic (to avoid leaking internal info up).
  * **Do not use** generic `Exception` or `RuntimeError` unless it’s a truly unexpected scenario or you're rethrowing after catching a low-level error (even then, consider wrapping in a custom exception). The goal is that upper layers can catch specific exceptions and handle them (e.g. the controller knows to turn a `ValidationException` into a 400 response).
* **Handling Exceptions:**

  * At **repository level** (infrastructure): catch database driver exceptions (e.g. `PyMongoError`) and raise a `MongoException` or return a failure indicator. Do not let driver exceptions bubble up.
  * At **service/use case level** (application): catch exceptions from repositories or adapters.

    * If it’s a `ValidationException` or `NotFoundException` from domain logic, you might let it propagate upward after logging, since it’s part of the expected flow (the controller or task will handle it).
    * If it’s a `MongoException` or other system exception, decide if you want to handle it (log and raise a generic `RuntimeError` to avoid exposing details) or let it bubble (which likely ends up as a 500).
    * Always log exceptions when caught, including context and `error: str(e)` in the extra. This ensures stack traces or at least error messages are recorded.
  * At **controller level** (interfaces): catch all expected exceptions from use cases:

    * For known business exceptions (Validation, NotFound), return appropriate responses (with error message for Validation, or a generic "not found" message).
    * Log these at warning level (since they are not system failures, just business flow issues). E.g., `logger.warning("Validation error during X", extra={"error": str(e), ...})`.
    * Catch unexpected exceptions (perhaps anything not recognized) and log at error level with traceback, then return a 500 response.
    * Utilize Flask error handlers if set up, or do try/except in each endpoint as needed to ensure no uncaught exception crashes the app without a response.
  * At **task level:** as described, catch and log exceptions, and use Celery retry or failure mechanisms as appropriate. You typically *do not* want to suppress exceptions in tasks unless you handle them; unhandled exceptions mark the task as failed which is usually desirable for alerting/retry.
* **Consistency in Exception Use:** When writing new code, prefer raising the existing custom exceptions rather than new ones, if it semantically fits the error:

  * E.g., if a new repository fails to find a record, raise `NotFoundException` (or return None and let service raise it).
  * If an external API call fails in an expected way (rate limit, etc.), you might wrap it in a `ValidationException` if it's due to bad input, or a new custom exception if it's a distinct category (but then handle that appropriately).
  * Avoid raising raw `AssertionError` or using `assert` for flow control in production code; use exceptions so they can be managed.
* **Flow of Exceptions:** Design the flow such that:

  * Domain raises exceptions for domain issues.
  * Application catches domain exceptions if it needs to add context or convert them, or lets them pass up if the interface layer can directly handle them.
  * Infrastructure raises exceptions for technical issues, which application might catch and convert to a generic failure (or log and propagate if we consider it fatal).
  * The interface is the final catch-all that ensures the user gets a response and the error is logged.
* **Fail Fast, Fail Loud:** It's better to raise an exception when something is wrong than to let it pass silently. For instance, if an unexpected state is encountered in a use case, log error and raise. Do not just return None or false without logging, as that can mask issues. Every failure should be traceable via logs.
* **Resource Cleanup:** If your code opens resources (files, network connections), use try/finally or context managers to ensure they close even on exceptions. This is more of a low-level concern, but worth noting in long-running tasks or adapters.

## Dependency Injection and Configuration

* **AppContainer Usage:** The project uses a custom `AppContainer` (based on `dependency_injector.containers.DeclarativeContainer`) defined in `app/main.py` (or similar). Always integrate new dependencies through this container:

  * When you create a new repository or adapter, add a provider for it in the container. Typically use `providers.Factory` for classes that should be instantiated each time they're requested, or `providers.Singleton` if a single instance is sufficient (most repositories are stateless, so Factory is fine; adapters with external connections might be singletons to reuse connections).
  * For new services or use cases, register them in the container after their dependencies. E.g., if you add `XService` or `XUseCase`, add something like `x_service = providers.Factory(XService, dep1=dep1_provider, dep2=dep2_provider, ...)` and `x_use_case = providers.Factory(XUseCase, x_service=x_service, other_dep=other_dep)`. Ensure names match the attribute used to retrieve them (`container.x_use_case()` will call that Factory).
  * **Order matters:** In the container, typically you define config first, then database, then repositories, then adapters, then services, then use cases, then event handlers. Follow the existing ordering so that each provider’s dependencies are already defined above it.
  * Use `providers.Configuration()` to access config values (like API keys, URLs). Make sure any new config key (if needed) is added to the Flask app config (perhaps via environment variables) and then referenced in the container’s config section.
* **No Manual Instantiation in Upper Layers:** Controllers and tasks should **always** use `current_app.config["container"]` to get instances, instead of instantiating classes themselves. This ensures that if we swap implementations (e.g. a different repository for tests or a different adapter for a new provider), the change is made in one place (the container) and everything picks it up.
* **Avoid Global State:** Outside the container, avoid using module-level singletons or global variables for dependencies. The container is the authoritative place for shared instances. For example, do not create a global database connection in a module; use `Database.initialize` via container.
* **Configuration Management:**

  * All configuration (DB URIs, API keys, external URLs, etc.) should come from the Flask `app.config` (populated likely from environment variables or config files). The container’s `providers.Configuration()` maps to `app.config`.
  * If new config entries are needed, add them to your config (like in a `Config` class or directly in the Flask app config loading). Then reference them in container as `container.config.some_key`.
  * Do not scatter `os.getenv` calls throughout the code. Fetch environment variables only in the configuration setup (to populate Flask config), not in random places in application logic.
* **Injecting Specific Components:** If a use case needs an external adapter (say a third-party client), don’t call it directly in the use case. Instead, inject it via container. e.g. container might provide `some_api_client = providers.Factory(SomeAPIClient, api_key=config.api_key)` and then the use case is `providers.Factory(NewFeatureUseCase, api_client=some_api_client, other_deps=...)`.
* **Flask App Context:** `current_app.config["container"]` is used in tasks and controllers. Ensure that:

  * In tasks, the Celery app is initialized with the Flask app’s context (the code does `celery = init_celery(app)` linking Flask and Celery). This means `current_app` inside a task refers to a proxy of the Flask app, and thus `config["container"]` is available. Always verify that tasks have access to needed config; if not, consider passing necessary config values as arguments.
  * Domain and application layers **should not** use `current_app` at all. The one exception seen is some use cases accessing `flask.g` for correlation\_id, which is tolerated for logging context. But never rely on `current_app` for config inside core logic; instead, any config needed (like a feature flag or constant) should be injected through the container or passed as an argument.
* **Adding New Dependencies:** When introducing a new library or integration, configure it similarly:

  * For example, adding a new message broker client: set up its config in Flask (host, credentials), add a provider in container (maybe as a singleton), then inject that into wherever needed (service or adapter).
  * This decouples the usage from the instantiation and allows easy switching or mocking.
* **Event Handlers via Container:** As part of DDD, if new domain events and handlers are introduced:

  * Define the event in domain (as mentioned), then create a handler class (most likely in the application layer or infrastructure if it deals with an external system). For instance, a `SendNotificationOnEvent` handler that uses an EmailAdapter.
  * Register the handler in the container (e.g. `send_notification_handler = providers.Singleton(SendNotificationOnEventHandler, email_adapter=email_adapter)`).
  * Subscribe the handler to the event via the EventDispatcher using `providers.Resource` or a similar mechanism as done with `subscribe_message_handlers` (this ensures the subscription happens at app startup).
  * This approach keeps event subscription configuration in one place (the container) and still respects boundaries (the handler itself will be in app layer or infra and will call adapters).
* **No Direct Flask App Usage:** Reiterating: do not import the Flask app object into domain or application code. If absolutely needed (rarely), pass things through function parameters or container. The Flask app (and things like `request` or `session`) should be confined to the interface layer.
* **Consistency:** The container is central to how the project is wired. Always update it when you add something new, and follow the style of definitions already there (notice how similar things are grouped and logged). If you remove or change something, update container accordingly. A mismatch (like forgetting to provide a new dependency) will cause runtime errors when the assistant tries to use it.

## Utilities and Common Patterns

* **Location for Helpers:** All general-purpose helper functions and definitions should live under `app/utils/**`. This includes:

  * **Exceptions:** `app/utils/exceptions/**` for custom exceptions (as covered above).
  * **Decorators:** `app/utils/decorators/**` for Flask or function decorators (e.g. JSON body validation, auth checking, Celery availability checks). Use these to keep controllers clean. If adding a new decorator, follow patterns (use `functools.wraps`, access Flask globals carefully, log appropriately).
  * **Tools/Utilities:** `app/utils/tools/**` for small helper functions (e.g. datetime helpers like `default_execute_at()` which adds one minute, `is_execute_at_in_future()` to compare times, or string/format helpers).
  * **Logging Setup:** If there are custom logging formatters or handlers (like `MongoDBHandler` for logging), those are also in utils or infra. Ensure any new logging utility is integrated properly (if you add one, register it in logging config as needed).
* **Adding New Utilities:** Before writing a new utility function, check if it already exists or if existing utilities cover your need. Avoid duplicating logic. For example, if you need to clean a response or convert a type, see if `response_cleaner.py` or `convert_value.py` has something similar.

  * If you must add a new function, place it in a logical submodule under `app/utils` (create one if necessary). Document it with a clear docstring, explaining purpose and usage.
  * Keep utility functions **pure** (no side effects) whenever possible. They should operate on input and return output without altering global state (exceptions: logging or generating UUIDs, which are side-effectish but necessary).
* **Decorators Usage:** Use the provided decorators to enforce rules:

  * e.g., `@auth_required` (if exists) for protected routes, `@validate_json_body` for ensuring JSON payload and content type, `@check_celery_queue_status` for endpoints that depend on Celery being up.
  * When writing new controllers, remember to apply these as needed rather than re-writing the logic inside the function.
  * If modifying or creating decorators, be careful not to introduce tight coupling with layers. For example, a decorator should not directly call repository or use case (that would break layering if utils ends up calling app code). It should stick to interface concerns (like checking Flask globals, headers, etc.).
* **Common Patterns to Follow:**

  * **DTO Conversion:** Many DTO classes have similar `from_dict` methods. If adding a DTO, implement a `from_dict(cls, data: dict)` that filters relevant keys and constructs the DTO. This is a common pattern in the code to conveniently go from raw dict (e.g. request JSON) to DTO object.
  * **Mapping Functions:** Repositories often have helper functions `_doc_to_entity`. Follow that convention for new repositories to keep mapping logic separate and testable.
  * **Status Flags and Enums:** If the domain uses certain constants (like status strings, or types), ensure you reference or extend them consistently. For instance, if `Message.status` can be `"queued"`, `"completed"`, etc., and you introduce a new status, add it in the appropriate place (domain model or config) and handle it in logic similarly to others.
  * **Celery Task Names and Binding:** All Celery tasks have unique names and often include `bind=True`. Make sure new tasks do as well, to maintain consistency and allow self-retry. The naming scheme (`task_entity_action` or similar) should be followed to avoid confusion.
  * **JSON Serialization:** When returning domain objects via API or task results, convert them to dict (using dataclasses.asdict or a custom method) rather than returning the object directly. This ensures no serialization issues. Check how existing code (like tasks or controllers) convert objects to JSON (they often use `asdict()` on dataclass instances).
  * **Time and Timezones:** If dealing with datetimes, use UTC consistently. The code uses `datetime.utcnow()` and timezone aware comparisons in some utils. If scheduling future tasks, ensure you timezone-aware `eta` as in the example (`eta = execute_at.replace(tzinfo=timezone.utc)`).
* **Naming Conventions:** Adhere to naming conventions observed:

  * Modules and file names: lowercase with underscores (e.g. `lead_repository.py`, `assistant_controller.py`).
  * Classes: PascalCase (e.g. `LeadRepository`, `AssistantService`).
  * Functions and methods: snake\_case (e.g. `create_assistant_type`, `get_all_assistants`).
  * Constants: all caps (if any config constants in code).
  * Logger names: kebab-case or descriptive strings (often with hyphens or words separated by dashes or underscores to identify the component in logs).
  * Try to use English for identifiers and messages (the codebase mixes some Spanish in comments/logs, but moving forward, prefer English for consistency unless otherwise specified).
* **Code Style:** Write code that is clean and conforms to PEP8:

  * Indentation 4 spaces, proper spacing around operators, etc.
  * Keep line length reasonable (\~100-120 chars to improve readability, as seen in the project).
  * Use type hints for function signatures and return types throughout application and domain code. The project already uses typing (Optional, List, Dict, etc.) – continue this for new code to improve clarity and enable static checks.
  * Add docstrings for classes, methods, and functions explaining their purpose, especially in the domain, services, and use cases. Many existing ones have docstrings – follow that practice.
* **Testing Considerations:** Though not directly part of the codebase files, ensure your code design allows easy testing:

  * Example: use cases and services should rely on interfaces (so you can provide fake implementations for tests).
  * Avoid static or hard-coded dependencies that can't be swapped out.
  * The architecture in place (with injection and layering) is built for testability, so continue in that vein for new code.

## Adding New Features: Step-by-Step Guide

When implementing a new feature or making a significant change, use the following workflow to maintain architectural consistency:

1. **Identify the Scope:** Determine what domain concepts the feature involves and what the nature of the feature is (new entity? new operation on existing entities? external integration?). This will tell you which layers will need changes or additions:

   * New business concept → likely need new Domain entity and repository interface.
   * New kind of operation → likely need new Use Case (application layer) and maybe new service method.
   * External system integration → likely need new Infrastructure adapter/client.
   * New API endpoint → need new Interface controller (and possibly tasks).
2. **Design the Domain Changes:** If a new domain entity or value object is required, create it under `app/domain/entities/<domain>/`. Define its fields (use `@dataclass` if appropriate) and any critical business methods. Ensure it has no dependencies on other layers.

   * If persistence is needed for it, also define a corresponding **repository interface** in `app/domain/repositories/<domain>/<entity>_repository.py` with the necessary abstract methods.
   * Consider if this entity will produce any **domain events** (e.g., “X created” event). If so, define those event classes in `app/domain/entities/<domain>/events/` and possibly update the EventDispatcher usage.
   * Example: Adding a "Project" entity → create `app/domain/entities/project/project.py` and `app/domain/repositories/project/project_repository.py` with methods like create, update, find\_by\_id, etc.
3. **Implement Infrastructure Support:** Provide concrete implementations for domain ports:

   * Implement the repository interface in `app/infrastructure/repositories/<domain>/` (e.g., `MongoProjectRepository` for `ProjectRepository`). Follow the existing repository patterns (init with `Database.get_db()`, implement methods with try/except around DB calls, mapping documents to entities).
   * If integrating a new external service, create an adapter in `app/infrastructure/adapters/` (you might create a subfolder if it’s complex). For instance, `app/infrastructure/adapters/payment/payment_adapter.py` for a payment API. Implement methods to perform the needed actions (API calls), and handle errors (raising custom exceptions on failure).
   * Add any needed config for these in Flask configuration (e.g., API keys as env vars) and ensure they are wired through the container (we’ll do that in a later step).
   * Reuse `app.utils` helpers if applicable (for example, use existing HTTP request utils or JSON cleaners if provided).
4. **Update/Create DTOs:** Determine what data needs to be passed from the interface to the application:

   * If new inputs or outputs are introduced (e.g., a new request body or a new structure returned), create DTO classes in `app/application/dtos/<domain>/` to represent them. For existing domains, it might be adding a new field to an existing DTO or creating a parallel DTO for new operations.
   * Example: For a new "Project" entity, create `ProjectCreateDTO`, `ProjectUpdateDTO` in `app/application/dtos/project/`. Include fields needed and default values if any. Provide `from_dict` for convenience.
   * Use DTOs in use case and service methods instead of raw dicts for clarity and validation.
   * If the feature interacts with external data formats (e.g., webhooks or third-party payloads), consider DTOs or Pydantic models in the adapter layer to parse those, keeping your application DTOs focused on your system’s view.
5. **Application Layer – Services:** If the feature domain has an associated service (likely yes if it’s an entity or major logic):

   * Create a service class in `app/application/services/<domain>/` or extend an existing one if it’s a new operation on an existing entity.
   * Implement methods in the service for the needed operations. For a new entity, typical methods would be `create_<entity>`, `update_<entity>`, `delete_<entity>`, `get_<entity>` etc., similar to patterns in other services.
   * These methods should:

     * Accept either DTOs or basic types, and output domain entities or basic results.
     * Use the injected repository (and possibly other repositories or adapters) to perform the operation.
     * Contain any business logic validations: e.g., check if something already exists, enforce invariants, raise `ValidationException` or `NotFoundException` as needed.
     * Log important actions and errors with context.
     * Not call any Flask or Celery stuff – remain business-focused.
   * If the operation involves multiple domain aggregates (e.g., create a Project also needs to create initial Tasks list, etc.), coordinate that here or in the use case (depending on complexity).
   * Test the service in isolation to ensure correctness of logic.
6. **Application Layer – Use Case:** Develop a use case class if the feature is a distinct workflow or user action:

   * Place it in `app/application/use_cases/<domain>/` (or create a new subfolder if domain is new).
   * Inject the necessary services, repository interfaces, and adapters via the constructor.
   * Implement public method(s) that the interface layer or tasks will call. If it’s a simple action, a single method `execute()` might suffice; if multiple operations (like separate methods for create/update), implement those.
   * The use case method should mostly delegate to service methods, but it can incorporate cross-entity logic or high-level sequencing:

     * E.g., a `RegisterUserUseCase.execute` first checks existing user via repository, creates if none, then uses `OTPService` to send OTP.
     * Ensure to catch exceptions from the service or domain and decide: either handle (e.g., log and return a specific result like False) or propagate further.
   * Use the use case to orchestrate external calls if needed: e.g., use an OpenAI adapter to get some result and then use a repository to store it.
   * **Domain Events:** If your operation should trigger a domain event (like something completed), consider dispatching it here via `EventDispatcher.dispatch(EventClass(...))`. The EventDispatcher is likely a singleton in domain; if not globally accessible, it might be provided via container (as seen with `event_dispatcher` provider).
   * **Logging:** As with others, log the start, important decisions, and end of the use case with relevant details and correlation id if available (though avoid using `flask.g` here; better to pass correlation id in from controller if needed or get via container if stored).
7. **Wire Up the Container:** Open the `AppContainer` definition (likely in `app/main.py` or `app/container.py`) and register all new components:

   * Add new configuration keys if any (e.g., `config.some_api_key = providers.Configuration('some_api_key')` if you set `app.config['SOME_API_KEY']` from env).
   * Ensure the database initialization (if needed for a new collection) is handled by existing `Database.initialize` (likely no change needed if using same DB).
   * Register the new **repository**: e.g., `project_repository = providers.Factory(MongoProjectRepository)`. If the repository requires constructor args (some do, but usually they just get DB from global `Database`), include them.
   * Register the new **adapter/client** if any: e.g., `payment_adapter = providers.Factory(PaymentAdapter, api_key=config.some_api_key, url=config.some_api_url)`.
   * Register the new **service**: e.g., `project_service = providers.Factory(ProjectService, project_repository=project_repository, other_dep=...)`.
   * Register the new **use case**: e.g., `project_use_case = providers.Factory(ProjectUseCase, project_service=project_service, another_service=..., external_client=...)`.
   * If the feature involves **event handlers**: e.g., `ProjectCompletedEvent` and a handler `ProjectCompletedHandler`, you would also:

     * Register the handler: `project_completed_handler = providers.Singleton(ProjectCompletedHandler, some_adapter=..., etc.)`.
     * Subscribe it to the event: e.g., `providers.Resource(lambda handler: EventDispatcher.subscribe(ProjectCompletedEvent, handler.handle_event), project_completed_handler)`.
   * Keep the naming consistent and add logging (`logger.info("... configured")`) similar to existing lines for traceability.
   * After updating, the container should be able to provide the new use case via `container.project_use_case()` and so forth.
8. **Add Interface Endpoints or Commands:** If exposing via HTTP API:

   * Create a new controller file under `app/interfaces/controllers/<domain>/` if one doesn't exist, or add to an appropriate existing controller.
   * Define a Flask Blueprint or route for the new endpoint. E.g., `@assistant_bp.route('/projects', methods=['POST'])` for creating a Project.
   * In the route function:

     * Parse `request.json` or other input.
     * Use `validate_json_body` decorator if a specific schema is expected (you might need to adjust it or ensure the JSON keys match your DTO).
     * Construct a DTO or required parameters. For example: `data = request.get_json(); dto = ProjectCreateDTO.from_dict(data)`.
     * Call the use case via container: `project = current_app.config["container"].project_use_case().create_project(dto)` (or `.execute(dto)` depending on your naming).

       * If the operation should be async, instead call the corresponding Celery task: e.g. `task_create_project.delay(data)` and possibly handle immediate response vs. deferred result as described earlier.
     * Handle the response: if synchronous, format the resulting domain object into a dict or use a response DTO, then return `standard_response(True, 201, "Project created", result_data)`.

       * If the use case raised a `ValidationException` or similar, catch it and return `standard_response(False, 400, str(e))`.
       * If `NotFoundException` (shouldn't typically happen on create, but maybe on update), return 404.
       * If async, you might return 202 Accepted with a message like "Task submitted" and maybe the task ID or some link to check status.
     * Set the appropriate HTTP status code as per REST conventions (201 for creation, 200 for normal success, 202 for accepted, 400/404 for client errors, 500 for server errors).
     * **Attach correlation id** to log messages: e.g., `logger.info("Received request to create project", extra={"correlation_id": g.correlation_id})`.
   * If the interface is not HTTP (maybe a CLI or background consumer), adapt accordingly, but still follow the pattern of minimal logic at the entrypoint and delegation to use cases.
   * Register the blueprint in `app/interfaces/routes.py` if it's a new controller, so the endpoints become active.
9. **Implement Celery Task (if needed):** For long-running parts of the feature:

   * Create a new task module in `app/task/<domain>/` (or add to an existing module if it relates).
   * Define a Celery task function with `@celery.task` decorator. e.g., `@celery.task(name="task_create_project", bind=True, autoretry_for=(Exception,), max_retries=5, default_retry_delay=300)` etc.
   * The task function will likely take primitive parameters or a dict (since Celery needs serializable args). It could take the project data dict, or an ID, etc.
   * Inside, similar to earlier guidelines: get container use case or service, create DTO if needed, call the logic, handle exceptions with retry.
   * Log the outcome. Return result if another step will use it (or if the controller is waiting for the result).
   * Example: `def task_create_project(self, project_data: dict):` ... create DTO, call use\_case, handle exceptions.
   * If chaining tasks (like after creating a project, maybe schedule another task to send a notification), use `apply_async` at the end of the first task.
   * Add the task module path to Celery initialization if not already included (in `init_celery`, there’s a list of imports; make sure your new task module is listed so Celery can find it).
10. **Testing & Validation:** Once implemented:

    * Write unit tests for new domain logic (if any), service methods, and use case flows. Use dependency injection to substitute real DB or external calls with mocks/fakes.
    * Test the integration via controllers (possibly using Flask test client or similar) to ensure the request through to response works as expected.
    * If possible, test Celery tasks by calling them synchronously (Celery provides `.run()` method on task functions for testing logic without a broker).
    * Verify logging output manually or via tests to ensure important events are logged (this is critical in absence of direct debugging).
    * Check that exceptions are propagated or handled correctly by simulating error conditions.
    * Ensure that adding this feature didn’t break existing conventions: run linting/format checks.
11. **Review for Separation of Concerns:** Before finalizing, go through your code:

    * Ensure no layer bleed-through: e.g., no accidental use of `requests` or DB calls in use case, no Flask `request` usage in service, etc.
    * Confirm that each new class is in the correct folder and namespace.
    * Validate naming consistency and refactor any misnamed variables or functions to match project style.
    * Remove any leftover debug code or prints (should use logging).
    * Make sure all new public methods have docstrings explaining their behavior and any assumptions.
12. **Adhere to Existing Patterns – No Alternatives:** This project has a well-defined way of doing things. Do not introduce:

    * New architectural styles (e.g., don’t suddenly use Active Record pattern or a different ORMs bypassing the repository approach).
    * Different task queues or schedulers (stick to Celery, don’t add e.g. RQ or threading for background jobs).
    * Bypassing the container (no manual singletons or direct calls to global objects).
    * Any quick hacks that violate layers (like a controller directly manipulating a database for convenience – it must go through use case).
    * If a change in pattern is absolutely needed, discuss it, but generally any such change is outside the scope of normal feature additions.
    * The goal is **uniformity**: any contributor or the AI assistant reading this should follow the same conventions so that all code looks like it was written following the same playbook.

