---
applyTo: 'app/application/services/message/context_strategies/**'
---

## Context Strategies Architecture Rules

This document defines the patterns, conventions, and architectural rules for implementing message context strategies in the setter-service application. These rules ensure consistency, maintainability, and extensibility of the context system.

## Overview

Context strategies are responsible for extracting and formatting specific pieces of information from message entities to provide context for AI assistant responses. The system supports both single and multiple strategy execution with ordered composition.

## Core Architecture Principles

### **Strategy Pattern Implementation**
* All context strategies must inherit from `MessageContextStrategy` abstract base class
* Each strategy implements a single `get_text(message: Message) -> str` method
* Strategies should be stateless and pure (no side effects except logging)
* Each strategy has a single responsibility and handles one specific type of context

### **Multi-Strategy Support**
* The system supports `List[TypeContext]` for applying multiple strategies in order
* `CompositeContextStrategy` combines multiple strategies and applies them sequentially
* Individual strategies can be used standalone or as part of a composition
* Order of execution is determined by `TypeContext.order` field

### **Fail-Fast Behavior**
* If any strategy in a composite fails, the entire operation fails
* Strategies should handle their own validation and return empty strings for invalid inputs
* No silent failures - always log errors and either return empty string or raise exceptions

## Strategy Naming Conventions

### **File Naming**
* Use snake_case with descriptive names: `last_message_context_strategy.py`
* Include the data source and type: `[source]_[type]_context_strategy.py`
* Examples: `last_response_fragment_context_strategy.py`, `pre_context_strategy.py`

### **Class Naming**
* Use PascalCase with `ContextStrategy` suffix: `LastMessageContextStrategy`
* Class name should clearly indicate the data source and purpose
* Avoid abbreviations - use full descriptive names

### **Factory Registration**
* Use SCREAMING_SNAKE_CASE for strategy type constants: `"LAST_MESSAGE"`
* Names should be self-explanatory and match the strategy purpose
* Register all strategies in `MessageContextFactory.get_strategy()` method

## Data Field Mapping

### **Message Entity Fields**
The following fields are available in the `Message` entity for context extraction:

| Field | Type | Purpose | Example Strategies |
|-------|------|---------|-------------------|
| `message` | `str` | User's input message | `LastMessageContextStrategy` |
| `response` | `Optional[str]` | Assistant's response | `LastResponseContextStrategy` |
| `response_fragment` | `List[str]` | Response pieces | `LastResponseFragmentContextStrategy` |
| `response_finetuning` | `List[str]` | Fine-tuned response parts | `LastResponseFinetuningContextStrategy` |
| `lead.prospect.precontext` | `str` | Pre-context information | `PreContextStrategy` |
| `assistant_response.name` | `str` | Assistant identifier | Used in response strategies |

### **Field Processing Rules**
* **String Fields**: Use directly with `or ""` fallback for None values
* **List Fields**: Combine using `"".join(list_field)` for concatenation
* **Nested Fields**: Always check for None at each level before accessing
* **Assistant Names**: Extract from `message.assistant_response.name` with empty string fallback

## Output Format Standards

### **JSON Response Format**
For strategies returning JSON, use this standard structure:

```python
result = {
    "user_message": content,      # For user messages
    "system_response": content    # For assistant responses
}
json_content = json.dumps(result, ensure_ascii=False, indent=appropriate_indent)
```

### **Labeled Format**
For strategies with labels, use this pattern:

```
<LABEL>: 
{
  "field_name": "content"
}
```

### **Specific Format Examples**

#### **User Message Format (LastMessageContextStrategy)**
```
USER_AGENT: 
{
  "user_message": "<MESSAGE_CONTENT>"
}
```

#### **Assistant Response Format (LastResponseContextStrategy)**
```
<ASSISTANT_NAME>:
{
    "system_response": "<RESPONSE_CONTENT>"
}
```

#### **Last Reason Format (LastReasonContextStrategy)**
```
<ASSISTANT_NAME>:
{
    "system_reason": "<REASON_CONTENT>"
}
```

#### **Pre-context Format (PreContextStrategy)**
```
<ASSISTANT_NAME>: <PRECONTEXT_MESSAGE>
```

#### **Combined Format (LastMessageAndResponseContextStrategy)**
```
USER_AGENT: 
{
  "user_message": "<MESSAGE_CONTENT>"
}

<ASSISTANT_NAME>:
{
    "system_response": "<RESPONSE_CONTENT>"
}
```

#### **Thread Format (AllMessagesContextStrategy)**
```
THREAD:

USER_AGENT: 
{
  "user_message": "<MESSAGE_CONTENT>"
}

<ASSISTANT_NAME>:
{
    "system_response": "<RESPONSE_CONTENT>"
}

USER_AGENT: 
{
  "user_message": "<NEXT_MESSAGE>"
}

<ASSISTANT_NAME>:
{
    "system_response": "<NEXT_RESPONSE>"
}
```

## Implementation Guidelines

### **Strategy Implementation Template**
```python
import json
from app.application.services.message.context_strategies.message_context_strategy import MessageContextStrategy
from app.domain.entities.message.message import Message

class NewContextStrategy(MessageContextStrategy):
    def get_text(self, message: Message) -> str:
        """
        Returns the [description] in the format:
        [Expected output format]
        
        Args:
            message: The message entity to extract [data] from
            
        Returns:
            Formatted string with [description of output]
        """
        # Validate and extract data
        content = message.field_name or ""
        
        # Get assistant name if needed
        assistant_name = ""
        if message.assistant_response and message.assistant_response.name:
            assistant_name = message.assistant_response.name
        
        # Format output
        result = {
            "field_name": content
        }
        json_content = json.dumps(result, ensure_ascii=False, indent=4)
        return f"{assistant_name}:\n{json_content}\n"
```

### **Validation Rules**
* Always check for None values before accessing nested properties
* Use `or ""` or `or []` for default values
* Handle empty collections gracefully
* Log warnings for unexpected data states but don't fail

### **JSON Formatting Standards**
* Use `ensure_ascii=False` to support non-ASCII characters
* Apply consistent indentation: `indent=2` for compact, `indent=4` for readable
* Always include trailing newlines where appropriate
* Use consistent field names: `"user_message"` and `"system_response"`

## Factory Integration

### **Adding New Strategies**
1. **Import the Strategy**: Add import in `MessageContextFactory`
2. **Register in Factory**: Add mapping in `get_strategy()` method
3. **Use Descriptive Constants**: Follow naming conventions
4. **Test Integration**: Ensure factory returns correct strategy instance

### **Factory Method Pattern**
```python
elif type_context == "NEW_STRATEGY_TYPE":
    return NewContextStrategy()
```

### **Dependencies**
* Strategies requiring `MessageService` must accept it in constructor
* Use dependency injection pattern for external dependencies
* Keep strategies lightweight - heavy logic belongs in services

## Composite Strategy Rules

### **CompositeContextStrategy Behavior**
* Applies strategies in the order specified by `TypeContext.order`
* Combines outputs with double newline separation (`\n\n`)
* Fails fast if any individual strategy fails
* Returns combined text from all successful strategies

### **Usage Patterns**
* Single strategy: Return strategy directly from factory
* Multiple strategies: Wrap in `CompositeContextStrategy`
* Empty list: Return `DefaultContextStrategy`

## Error Handling

### **Strategy-Level Errors**
* Return empty string for invalid input rather than raising exceptions
* Log warnings for unexpected conditions
* Use defensive programming for None checks

### **Composite-Level Errors**
* If any strategy fails, the entire composite operation fails
* Preserve error information for debugging
* Log context about which strategy failed

### **Factory-Level Errors**
* Unknown strategy types return `DefaultContextStrategy`
* Log warnings for unrecognized strategy requests
* Never return None from factory methods

## Testing Guidelines

### **Unit Testing Requirements**
* Test each strategy independently with various message configurations
* Test null/empty value handling
* Test output format compliance
* Test factory registration and retrieval

### **Integration Testing**
* Test composite strategy behavior
* Test factory integration
* Test end-to-end context generation

### **Test Data Patterns**
* Create message fixtures with all field combinations
* Test edge cases (empty strings, null values, missing nested objects)
* Verify output format consistency

## Performance Considerations

### **Efficiency Rules**
* Strategies should be fast and lightweight
* Avoid heavy computations in context generation
* Cache expensive operations where appropriate
* Minimize memory allocations

### **Scalability**
* Strategies must handle large message volumes
* Avoid N+1 query patterns in strategies requiring database access
* Consider pagination for strategies processing multiple messages

## Documentation Standards

### **Code Documentation**
* All strategies must have comprehensive docstrings
* Document expected input and output formats
* Include usage examples in docstrings
* Document any special behavior or edge cases

### **Architectural Documentation**
* Update this document when adding new strategy types
* Document new output formats and patterns
* Maintain examples for all supported formats

## Migration and Backward Compatibility

### **Version Management**
* New strategies should not break existing functionality
* Changes to output formats require careful consideration
* Document breaking changes and migration paths

### **Legacy Support**
* Maintain support for existing strategy types
* Deprecate old strategies gracefully
* Provide migration guides for format changes

## Quality Assurance

### **Code Review Checklist**
- [ ] Strategy follows naming conventions
- [ ] Implements required abstract methods
- [ ] Includes comprehensive docstring
- [ ] Handles null/empty values safely
- [ ] Uses consistent output formatting
- [ ] Registered in factory correctly
- [ ] Includes appropriate tests
- [ ] Follows architectural patterns

### **Format Validation**
- [ ] JSON output uses correct field names
- [ ] Indentation is consistent
- [ ] Non-ASCII characters handled properly
- [ ] Labels and prefixes follow standards
- [ ] Newlines and spacing are correct

## Examples and Best Practices

### **Simple Strategy Example**
```python
class ExampleContextStrategy(MessageContextStrategy):
    def get_text(self, message: Message) -> str:
        content = message.some_field or ""
        return f"EXAMPLE: {content}"
```

### **Complex Strategy Example**
```python
class ComplexContextStrategy(MessageContextStrategy):
    def get_text(self, message: Message) -> str:
        # Validation
        if not message.some_field:
            return ""
        
        # Data extraction
        content = message.some_field
        assistant_name = ""
        if message.assistant_response and message.assistant_response.name:
            assistant_name = message.assistant_response.name
        
        # Format output
        result = {"field": content}
        json_content = json.dumps(result, ensure_ascii=False, indent=4)
        return f"{assistant_name}:\n{json_content}\n"
```

## Refactorization and Separation by Key Functionalities

### **Controller Refactorization**

Following Hexagonal Architecture and DDD principles, controllers have been refactored to separate concerns by key functionalities:

#### **Separation Principles**
* **Single Responsibility**: Each controller handles one specific domain or functionality
* **Feature-Based Organization**: Controllers are organized by business capabilities rather than technical layers
* **Clear Boundaries**: Each controller has well-defined responsibilities and dependencies

#### **Controller Structure**
```
app/interfaces/controllers/
├── assistant/
│   ├── assistant_controller.py          # Assistant management operations
│   ├── assistant_type_controller.py     # Assistant type configuration
│   └── assistant_flow_controller.py     # Assistant workflow management
├── message/
│   ├── message_controller.py            # Core message operations
│   ├── message_flow_controller.py       # Message flow orchestration
│   └── message_context_controller.py    # Context-specific operations
├── lead/
│   ├── lead_controller.py               # Lead management
│   └── lead_integration_controller.py   # External lead integrations
└── auth/
    ├── auth_controller.py               # Authentication operations
    └── otp_controller.py                # OTP-specific functionality
```

#### **Controller Responsibilities**
* **Core Controllers**: Handle CRUD operations and basic entity management
* **Flow Controllers**: Orchestrate complex workflows and multi-step processes
* **Integration Controllers**: Manage external system interactions
* **Specialized Controllers**: Handle specific business logic (context, configuration, etc.)

### **Task Refactorization**

Celery tasks have been organized by functional domains to improve maintainability and scalability:

#### **Task Organization Principles**
* **Domain Separation**: Tasks grouped by business domain
* **Functional Cohesion**: Related tasks kept together
* **Clear Dependencies**: Task dependencies explicitly defined
* **Scalable Structure**: Easy to add new tasks within domains

#### **Task Structure**
```
app/task/
├── assistant/
│   ├── __init__.py
│   ├── assistant_celery_task.py         # Assistant management tasks
│   ├── assistant_flow_task.py           # Assistant workflow tasks
│   └── assistant_context_task.py        # Context processing tasks
├── message/
│   ├── __init__.py
│   ├── message_celery_task.py           # Core message processing
│   ├── message_flow_task.py             # Message flow orchestration
│   └── message_analysis_task.py         # Message analysis and processing
├── lead/
│   ├── __init__.py
│   └── lead_integration_task.py         # Lead external integrations
└── thread/
    ├── __init__.py
    ├── thread_celery_task.py            # Thread management
    └── thread_flow_task.py              # Thread workflow tasks
```

#### **Task Responsibilities**
* **Core Tasks**: Basic entity operations and data processing
* **Flow Tasks**: Complex workflows requiring multiple steps
* **Integration Tasks**: External API calls and third-party integrations
* **Analysis Tasks**: Data processing, analytics, and reporting

### **Use Case Refactorization**

Use cases have been restructured to follow DDD bounded contexts and single responsibility principle:

#### **Use Case Organization**
* **Domain-Driven Structure**: Use cases organized by domain boundaries
* **Single Purpose**: Each use case handles one specific business operation
* **Clear Interfaces**: Well-defined input/output contracts
* **Testable Design**: Easy to unit test in isolation

#### **Use Case Structure**
```
app/application/use_cases/
├── assistant/
│   ├── __init__.py
│   ├── create_assistant_use_case.py     # Assistant creation logic
│   ├── update_assistant_use_case.py     # Assistant modification logic
│   ├── assistant_type_use_case.py       # Assistant type management
│   └── assistant_flow_use_case.py       # Assistant workflow coordination
├── message/
│   ├── __init__.py
│   ├── create_message_use_case.py       # Message creation
│   ├── process_message_use_case.py      # Message processing logic
│   ├── message_context_use_case.py      # Context generation logic
│   └── message_flow_use_case.py         # Message flow orchestration
├── lead/
│   ├── __init__.py
│   ├── create_lead_use_case.py          # Lead creation
│   ├── update_lead_use_case.py          # Lead modification
│   └── lead_integration_use_case.py     # Lead external operations
└── auth/
    ├── __init__.py
    ├── authenticate_user_use_case.py    # User authentication
    ├── register_user_use_case.py        # User registration
    └── otp_verification_use_case.py     # OTP verification logic
```

#### **Use Case Responsibilities**
* **Creation Use Cases**: Handle entity creation with all business rules
* **Update Use Cases**: Manage entity modifications and state changes
* **Flow Use Cases**: Orchestrate complex business processes
* **Integration Use Cases**: Coordinate with external systems

### **Benefits of Refactorization**

#### **Maintainability**
* **Easier Navigation**: Developers can quickly find relevant code
* **Reduced Coupling**: Clear separation reduces interdependencies
* **Focused Changes**: Modifications are contained within specific domains

#### **Scalability**
* Teams can work on different functionalities with minimal conflicts
* Clear ownership boundaries for different business domains
* Easier onboarding for new team members
* Parallel development of different features

#### **Architecture Compliance**
* Hexagonal Boundaries: Clear separation between layers
* DDD Principles: Bounded contexts are well-defined
* Single Responsibility: Each component has one clear purpose

### **Migration Guidelines**

#### **When Adding New Functionality**
1. **Identify Domain**: Determine which business domain the functionality belongs to
2. **Choose Appropriate Layer**: Decide if it's a controller, task, or use case concern
3. **Follow Naming Conventions**: Use consistent naming patterns
4. **Maintain Separation**: Don't mix concerns across different functionalities

#### **Refactoring Existing Code**
1. **Analyze Current Structure**: Understand existing dependencies
2. **Plan Migration**: Create migration strategy for large changes
3. **Maintain Backward Compatibility**: Ensure existing functionality continues to work
4. **Update Tests**: Modify tests to reflect new structure

### **Best Practices for Separation**

#### **Naming Conventions**
* Use descriptive names that indicate functionality
* Follow consistent patterns across similar components
* Include domain context in file names
* Avoid generic names like `handler.py` or `processor.py`

#### **Dependency Management**
* Keep dependencies within domain boundaries
* Use dependency injection for cross-domain interactions
* Avoid circular dependencies between domains
* Use interfaces for external dependencies

#### **Code Organization**
* Group related functionality together
* Separate concerns clearly
* Use appropriate abstraction levels
* Maintain consistent file structure across domains

## Conclusion

These rules ensure consistent, maintainable, and extensible context strategy implementation. All new strategies must follow these patterns to maintain system coherence and reliability. Regular review and updates of these rules ensure they remain current with evolving requirements.

## Controllers, Tasks, and Use Cases Separation by Key Functionalities

### **Architectural Refactoring Overview**

The application has been refactored to organize controllers, tasks, and use cases by key business functionalities rather than technical concerns. This separation follows Domain-Driven Design principles and improves maintainability, scalability, and team collaboration.

### **Separation Principles**

#### **Functionality-Based Organization**
* Controllers, tasks, and use cases are grouped by business domain capabilities
* Each functionality group contains related operations and workflows
* Cross-cutting concerns are handled through shared services and utilities
* Clear boundaries between different business domains

#### **Key Functionality Groups**

**Authentication & Security**
* Controllers: `app/interfaces/controllers/auth/`
* Tasks: `app/task/auth/`
* Use Cases: `app/application/use_cases/auth/`
* Responsibilities: User authentication, authorization, session management, OTP handling

**Lead Management**
* Controllers: `app/interfaces/controllers/lead/`
* Tasks: `app/task/lead/`
* Use Cases: `app/application/use_cases/lead/`
* Responsibilities: Lead creation, qualification, tracking, conversion workflows

**Message Processing**
* Controllers: `app/interfaces/controllers/message/`
* Tasks: `app/task/message/`
* Use Cases: `app/application/use_cases/message/`
* Responsibilities: Message handling, context generation, response processing

**Assistant Management**
* Controllers: `app/interfaces/controllers/assistant/`
* Tasks: `app/task/assistant/`
* Use Cases: `app/application/use_cases/assistant/`
* Responsibilities: Assistant configuration, behavior management, response generation

**Thread Management**
* Controllers: `app/interfaces/controllers/thread/`
* Tasks: `app/task/thread/`
* Use Cases: `app/application/use_cases/thread/`
* Responsibilities: Conversation thread handling, state management, continuity

**Node Operations**
* Controllers: `app/interfaces/controllers/node/`
* Tasks: `app/task/node/`
* Use Cases: `app/application/use_cases/node/`
* Responsibilities: Flow node processing, decision trees, workflow orchestration

**User Management**
* Controllers: `app/interfaces/controllers/user/`
* Tasks: `app/task/user/`
* Use Cases: `app/application/use_cases/user/`
* Responsibilities: User lifecycle, profile management, preferences

### **File Organization Patterns**

#### **Controller Structure**
```
app/interfaces/controllers/
├── auth/
│   ├── __init__.py
│   ├── login_controller.py
│   ├── registration_controller.py
│   └── otp_controller.py
├── lead/
│   ├── __init__.py
│   ├── lead_creation_controller.py
│   ├── lead_qualification_controller.py
│   └── lead_tracking_controller.py
├── message/
│   ├── __init__.py
│   ├── message_processing_controller.py
│   └── context_generation_controller.py
└── [other functionalities]/
```

#### **Task Structure**
```
app/task/
├── auth/
│   ├── __init__.py
│   ├── auth_celery_task.py
│   └── otp_celery_task.py
├── lead/
│   ├── __init__.py
├── message/
│   ├── __init__.py
│   ├── message_celery_task.py
│   └── context_celery_task.py
└── [other functionalities]/
```

#### **Use Case Structure**
```
app/application/use_cases/
├── auth/
│   ├── __init__.py
│   ├── login_use_case.py
│   ├── registration_use_case.py
│   └── otp_use_case.py
├── lead/
│   ├── __init__.py
│   ├── lead_creation_use_case.py
│   └── lead_qualification_use_case.py
├── message/
│   ├── __init__.py
│   ├── message_processing_use_case.py
│   └── context_generation_use_case.py
└── [other functionalities]/
```

### **Implementation Guidelines**

#### **Controller Organization Rules**
* Each controller file handles operations for a specific business capability
* Controllers within the same functionality folder can share DTOs and validation logic
* Cross-functionality communication goes through use cases, not direct controller calls
* Controllers are thin and delegate business logic to appropriate use cases

#### **Task Organization Rules**
* Tasks are grouped by the business domain they serve
* Async workflows within a functionality can be chained or orchestrated
* Tasks can call use cases from different functionalities when needed
* Background processing is organized by business intent, not technical implementation

#### **Use Case Organization Rules**
* Use cases represent complete business workflows or operations
* Each use case file contains related business operations
* Use cases can orchestrate services from multiple domains
* Dependencies between use cases in different functionalities should be minimal

### **Naming Conventions**

#### **File Naming**
* Use descriptive names that indicate the specific business capability
* Include the functionality type in the name: `lead_creation_controller.py`
* Maintain consistency across layers: similar operations have similar names
* Use snake_case for file names

#### **Class Naming**
* Follow PascalCase with descriptive business terms
* Include the layer type in class names: `LeadCreationController`, `MessageProcessingUseCase`
* Align class names with file names for easy navigation
* Use domain-specific terminology that business stakeholders understand

### **Cross-Functionality Communication**

#### **Service Layer Integration**
* Services in `app/application/services/` can be shared across functionalities
* Domain services handle cross-cutting business logic
* Infrastructure adapters are functionality-agnostic
* Repository patterns remain consistent across all functionalities

#### **Event-Driven Communication**
* Use domain events for communication between functionalities
* Events maintain loose coupling between business domains
* Event handlers can be organized by functionality or kept centralized
* Async event processing through Celery tasks

#### **Dependency Management**
* Use dependency injection through AppContainer
* Shared dependencies are configured at the container level
* Functionality-specific dependencies are scoped appropriately
* Avoid direct imports between functionality groups

### **Benefits of This Organization**

#### **Maintainability**
* Related code is co-located and easier to find
* Changes to a business domain are contained within its functionality group
* Reduced cognitive load when working on specific features
* Clear separation of concerns

#### **Team Collaboration**
* Teams can work on different functionalities with minimal conflicts
* Clear ownership boundaries for different business domains
* Easier onboarding for new team members
* Parallel development of different features

#### **Scalability**
* Easy to scale specific functionalities independently
* Clear extension points for new business capabilities
* Modular architecture supports microservices migration if needed
* Performance optimization can be targeted by functionality

### **Migration Guidelines**

#### **Existing Code**
* Legacy code should be gradually migrated to the new structure
* Start with the most active or critical functionalities
* Maintain backward compatibility during transition
* Update imports and dependencies incrementally

#### **New Features**
* All new features must follow the functionality-based organization
* Identify the primary business domain for new capabilities
* Create new functionality groups when existing ones don't fit
* Follow established patterns for controllers, tasks, and use cases

### **Quality Assurance**

#### **Code Review Checklist**
- [ ] Code is placed in the correct functionality group
- [ ] Naming conventions are followed consistently
- [ ] Dependencies between functionalities are minimal and well-defined
- [ ] Business logic is appropriately separated from technical concerns
- [ ] Cross-cutting concerns are handled through shared services

#### **Architectural Validation**
- [ ] New functionality groups have clear business justification
- [ ] Separation of concerns is maintained across layers
- [ ] Domain boundaries are respected
- [ ] Integration patterns are consistent with existing code


# AllReasonsContextStrategy Documentation

## Overview

The `AllReasonsContextStrategy` is a context extraction strategy that extracts all `reason` fields from all `SetterSteps` in a message, formatting them with assistant information according to the established context strategy patterns.

## Purpose

This strategy is designed to:
- Extract reasoning information from all steps in a message flow that contain reasons
- Provide structured context with step numbering and individual assistant identification
- Follow the consistent JSON formatting pattern used by other context strategies
- Handle cases where not all SetterSteps have reasons

## Implementation Details

### Location
- **File**: `app/application/services/message/context_strategies/all_reasons_context_strategy.py`
- **Class**: `AllReasonsContextStrategy`
- **Parent**: `MessageContextStrategy`

### Key Features

1. **All SetterSteps Processing**: Examines all `SetterSteps` in the message
2. **Selective Extraction**: Only includes SetterSteps that have a `reason` field
3. **Step Numbering**: Maintains original step order with step numbers
4. **Individual Assistant Names**: Tracks the assistant for each reason
5. **Primary Assistant Identification**: Uses the last assistant as the primary name
6. **Robust Handling**: Supports multiple response formats (dict, object with attributes, object with `__getitem__`)
7. **Graceful Degradation**: Returns empty string when no reasons are found

### Output Format

The strategy produces output in the following format:
```
<PRIMARY_ASSISTANT_NAME>:
{
    "system_reasons": [
        {
            "step": 1,
            "assistant": "<ASSISTANT_NAME_1>",
            "reason": "<REASON_1>"
        },
        {
            "step": 3,
            "assistant": "<ASSISTANT_NAME_3>",
            "reason": "<REASON_3>"
        }
    ]
}
```

Example:
```
GPT4Assistant:
{
    "system_reasons": [
        {
            "step": 1,
            "assistant": "AnalysisBot",
            "reason": "Initial analysis requires market data review"
        },
        {
            "step": 3,
            "assistant": "GPT4Assistant",
            "reason": "Final recommendation based on comprehensive analysis"
        }
    ]
}
```

### Method Signatures

#### `get_text(message: Message) -> str`
Main method that extracts and formats all reasons from SetterSteps.

**Parameters:**
- `message`: The message entity to extract reasons from

**Returns:**
- Formatted string with primary assistant name and JSON reasons content
- Empty string if no SetterSteps with reasons found

#### `_extract_all_reasons(setter_steps: List) -> List[Dict[str, Any]]`
Private helper method that extracts all reasons from the list of SetterSteps.

**Parameters:**
- `setter_steps`: List of SetterSteps to extract reasons from

**Returns:**
- List of dictionaries containing step info and reason

#### `_get_primary_assistant_name(setter_steps: List) -> str`
Private helper method that gets the primary assistant name from setter_steps.

**Parameters:**
- `setter_steps`: List of SetterSteps to get assistant name from

**Returns:**
- The primary assistant name (from last SetterSteps with assistant), or empty string

#### `_extract_reason_from_openai_response(openai_response) -> Optional[str]`
Private helper method that extracts the reason field from various openai_response formats.

**Parameters:**
- `openai_response`: The OpenAI response object or dict

**Returns:**
- The reason string if found, None otherwise

### Usage in Factory

The strategy is registered in `MessageContextFactory` with the identifier:
- **Type**: `"ALL_REASONS"`
- **Factory Method**: `get_strategy("ALL_REASONS")`

### Error Handling

The strategy includes comprehensive error handling for:

1. **Missing SetterSteps**: Returns empty string if `message.setter_steps` is None or empty
2. **No Reasons Found**: Returns empty string if no SetterSteps contain reasons
3. **Missing Assistant**: Handles cases where `node.assistant` is None (empty assistant name)
4. **Partial Data**: Skips SetterSteps without reasons, includes only those with valid reasons
5. **Various Response Formats**: Supports dict, object attributes, and object with `__getitem__`
6. **Exception Safety**: Gracefully handles KeyError, TypeError, and AttributeError

### Data Processing Logic

1. **Step Enumeration**: Each SetterSteps gets a step number (1-based indexing)
2. **Reason Filtering**: Only SetterSteps with valid reasons are included
3. **Assistant Extraction**: Individual assistant names are extracted per step
4. **Primary Assistant Selection**: The last SetterSteps with an assistant provides the primary name
5. **JSON Structure**: Results are formatted as an array of reason objects

### Testing

Comprehensive unit tests are available in:
- **File**: `tests/unit/test_all_reasons_context_strategy.py`
- **Integration Tests**: `tests/unit/test_message_context_factory_all_reasons.py`

Test coverage includes:
- Single and multiple SetterSteps scenarios
- Mixed scenarios (some steps with/without reasons)
- Missing data scenarios
- Various response formats
- Complex nested structures
- Unicode handling
- Assistant name resolution

## Architecture Compliance

### Hexagonal Architecture
- **Domain Layer**: Uses entities from `app.domain.entities`
- **Application Layer**: Implements business logic in application services
- **Interface**: Follows `MessageContextStrategy` contract

### SOLID Principles
- **Single Responsibility**: Focused solely on extracting all reasons and formatting
- **Open/Closed**: Extensible through inheritance, closed for modification
- **Liskov Substitution**: Fully substitutable for `MessageContextStrategy`
- **Interface Segregation**: Minimal, focused interface
- **Dependency Inversion**: Depends on abstractions, not concretions

### Design Patterns
- **Strategy Pattern**: Implements context extraction strategy
- **Template Method**: Follows established pattern from other context strategies
- **Factory Pattern**: Registered and created through `MessageContextFactory`

## Dependencies

- `app.application.services.message.context_strategies.message_context_strategy.MessageContextStrategy`
- `app.domain.entities.message.message.Message`
- `typing.Optional`, `typing.List`, `typing.Dict`, `typing.Any`
- `json` (for formatting)

## Integration

The strategy integrates seamlessly with:
- **MessageContextFactory**: For strategy creation and management
- **CompositeContextStrategy**: For multi-strategy compositions
- **Context Handler**: For runtime execution
- **Flow Executor**: For message processing workflows

## Use Cases

This strategy is particularly useful for:
- **Multi-step Reasoning Tracking**: Understanding the reasoning flow across multiple steps
- **Decision Audit Trails**: Maintaining records of all reasoning steps
- **Complex Workflow Analysis**: Analyzing reasoning patterns in complex message flows
- **Assistant Collaboration Tracking**: Understanding how different assistants contribute reasoning

## Best Practices

1. **Handle Sparse Data**: Not all SetterSteps will have reasons - filter appropriately
2. **Maintain Step Order**: Preserve the original step sequence in output
3. **Use Individual Assistant Names**: Each step can have a different assistant
4. **Primary Assistant Selection**: Use the most recent assistant as the primary identifier
5. **Defensive Programming**: Always check for data availability before extraction

## Performance Considerations

- **Linear Processing**: O(n) complexity where n is the number of SetterSteps
- **Memory Efficient**: Only stores reasons that exist, skips empty ones
- **Fast Filtering**: Early rejection of SetterSteps without reasons
- **Efficient JSON Serialization**: Uses standard library with appropriate settings
- **No Side Effects**: Pure function implementation

## Version History

- **v1.0.0**: Initial implementation with comprehensive error handling and testing

## Related Documentation


# OpenAI DTO Refactoring Documentation

## Overview
The OpenAI DTO classes have been refactored to improve code organization and comply with SOLID principles, specifically the Single Responsibility Principle (SRP).

## Changes Made

### Before (response_generic.py)
- All DTO classes were in a single file
- Violating SRP as each class had different responsibilities
- Harder to maintain and extend

### After (Separate Files)
- Each DTO class is now in its own file
- Better separation of concerns
- Easier to maintain and extend
- Follows SOLID principles

## File Structure

```
app/infrastructure/adapters/open_ai/dto/
├── __init__.py                     # Empty module (clean, no explicit imports)
├── response_extraction.py          # Base ResponseExtraction class
├── string_response.py             # StringResponse class
├── string_list_response.py        # StringListResponse class  
├── dict_response.py               # DictResponse class
├── metrics_response.py            # MetricsResponse class
├── metrics_extraction.py          # MetricsExtraction class (existing)
└── registry.py                    # Parser configuration (direct imports)
```

## Import Patterns

### Recommended Import (direct from specific modules)
```python
from app.infrastructure.adapters.open_ai.dto.string_response import StringResponse
from app.infrastructure.adapters.open_ai.dto.metrics_response import MetricsResponse
```

### Base Class Import
```python
from app.infrastructure.adapters.open_ai.dto.response_extraction import ResponseExtraction
```

### Legacy Import (no longer available)
```python
# OLD (removed)
from app.infrastructure.adapters.open_ai.dto.response_generic import StringResponse  # FILE REMOVED
```

## Benefits

1. **Single Responsibility**: Each file has one clear purpose
2. **Better Organization**: Related code is grouped logically
3. **Easier Testing**: Can test individual classes in isolation
4. **Cleaner Imports**: Clear import paths for each class
5. **Future Extensibility**: Easy to add new response types

## Migration Guide

No code changes are required for existing code that imports directly from specific modules. The registry.py has been updated to use direct imports.

For any code still using the old `response_generic.py` (now removed), update to direct imports:

```python
# OLD (file no longer exists)
from app.infrastructure.adapters.open_ai.dto.response_generic import StringResponse

# NEW (required)
from app.infrastructure.adapters.open_ai.dto.string_response import StringResponse
```

## Benefits of Clean __init__.py

1. **No Import Coupling**: Adding new DTO classes doesn't require modifying __init__.py
2. **Explicit Dependencies**: Each module imports exactly what it needs
3. **Better IDE Support**: Direct imports provide better autocomplete and navigation
4. **Reduced Circular Import Risk**: No central import hub reduces complexity
5. **Easier Maintenance**: Changes to one DTO don't affect the module structure

## Future Extensibility Example

To add a new DTO class (e.g., `BooleanResponse`), simply:

1. Create the new file:
```python
# app/infrastructure/adapters/open_ai/dto/boolean_response.py
from app.infrastructure.adapters.open_ai.dto.response_extraction import ResponseExtraction

class BooleanResponse(ResponseExtraction):
    response: bool
```

2. Use it directly where needed:
```python
# In registry.py or any other file
from app.infrastructure.adapters.open_ai.dto.boolean_response import BooleanResponse
```

No changes needed to:
- `__init__.py` (stays clean)
- Other DTO files  
- Existing imports

This demonstrates true extensibility and SOLID compliance.

## Cleanup Completed

The `response_generic.py` file has been removed as the refactoring is complete and all code has been migrated to the new structure.

## Related Documentation

- See `.github/instructions/architecture-rules.instructions.md` for general architecture principles
- See `.github/instructions/context-strategies-rules.instructions.md` for context strategy patterns


# LastReasonContextStrategy Documentation

## Overview

The `LastReasonContextStrategy` is a context extraction strategy that extracts the `reason` field from the last `SetterSteps` in a message, formatting it with the assistant's name according to the established context strategy patterns.

## Purpose

This strategy is designed to:
- Extract the reasoning information from the most recent step in a message flow
- Provide structured context with assistant identification
- Follow the consistent JSON formatting pattern used by other context strategies

## Implementation Details

### Location
- **File**: `app/application/services/message/context_strategies/last_reason_context_strategy.py`
- **Class**: `LastReasonContextStrategy`
- **Parent**: `MessageContextStrategy`

### Key Features

1. **Last SetterSteps Extraction**: Focuses on the most recent `SetterSteps` in the message
2. **Assistant Name Resolution**: Extracts assistant name from `setter_step.node.assistant.name`
3. **Reason Extraction**: Gets the `reason` field from `setter_step.openai_response["reason"]`
4. **Robust Handling**: Supports multiple response formats (dict, object with attributes, object with `__getitem__`)
5. **Graceful Degradation**: Returns empty string when data is missing or invalid

### Output Format

The strategy produces output in the following format:
```
<ASSISTANT_NAME>:
{
    "system_reason": <REASON>
}
```

Example:
```
GPT4Assistant:
{
    "system_reason": "The user requested a complex analysis that requires deep reasoning"
}
```

### Method Signatures

#### `get_text(message: Message) -> str`
Main method that extracts and formats the reason from the last SetterSteps.

**Parameters:**
- `message`: The message entity to extract reason from

**Returns:**
- Formatted string with assistant name and JSON reason content
- Empty string if no SetterSteps or reason found

#### `_extract_reason_from_openai_response(openai_response) -> Optional[str]`
Private helper method that extracts the reason field from various openai_response formats.

**Parameters:**
- `openai_response`: The OpenAI response object or dict

**Returns:**
- The reason string if found, None otherwise

### Usage in Factory

The strategy is registered in `MessageContextFactory` with the identifier:
- **Type**: `"LAST_REASON"`
- **Factory Method**: `get_strategy("LAST_REASON")`

### Error Handling

The strategy includes comprehensive error handling for:

1. **Missing SetterSteps**: Returns empty string if `message.setter_steps` is None or empty
2. **Missing Assistant**: Handles cases where `node.assistant` is None (empty assistant name)
3. **Missing Reason**: Returns empty string if no reason field is found
4. **Various Response Formats**: Supports dict, object attributes, and object with `__getitem__`
5. **Exception Safety**: Gracefully handles KeyError, TypeError, and AttributeError

### Testing

Comprehensive unit tests are available in:
- **File**: `tests/unit/test_last_reason_context_strategy.py`
- **Integration Tests**: `tests/unit/test_message_context_factory_last_reason.py`

Test coverage includes:
- Valid extraction scenarios
- Multiple SetterSteps (ensures last is used)
- Missing data scenarios
- Various response formats
- Complex nested structures
- Unicode handling

## Architecture Compliance

### Hexagonal Architecture
- **Domain Layer**: Uses entities from `app.domain.entities`
- **Application Layer**: Implements business logic in application services
- **Interface**: Follows `MessageContextStrategy` contract

### SOLID Principles
- **Single Responsibility**: Focused solely on reason extraction and formatting
- **Open/Closed**: Extensible through inheritance, closed for modification
- **Liskov Substitution**: Fully substitutable for `MessageContextStrategy`
- **Interface Segregation**: Minimal, focused interface
- **Dependency Inversion**: Depends on abstractions, not concretions

### Design Patterns
- **Strategy Pattern**: Implements context extraction strategy
- **Template Method**: Follows established pattern from other context strategies
- **Factory Pattern**: Registered and created through `MessageContextFactory`

## Dependencies

- `app.application.services.message.context_strategies.message_context_strategy.MessageContextStrategy`
- `app.domain.entities.message.message.Message`
- `typing.Optional`
- `json` (for formatting)

## Integration

The strategy integrates seamlessly with:
- **MessageContextFactory**: For strategy creation and management
- **CompositeContextStrategy**: For multi-strategy compositions
- **Context Handler**: For runtime execution
- **Flow Executor**: For message processing workflows

## Best Practices

1. **Always check for data availability** before extraction
2. **Use the helper method** for robust response parsing
3. **Follow the established JSON formatting** pattern
4. **Handle edge cases gracefully** with empty string returns
5. **Maintain consistent assistant name extraction** pattern

## Performance Considerations

- **Minimal Memory Footprint**: Only processes the last SetterSteps
- **Fast Execution**: Direct list access for last element
- **Efficient JSON Serialization**: Uses standard library with appropriate settings
- **No Side Effects**: Pure function implementation

## Version History

- **v1.0.0**: Initial implementation with comprehensive error handling and testing



# SetFinetuningService Refactoring Documentation

## Overview
The `SetFinetuningService` has been refactored to improve robustness, type safety, and error handling while maintaining SOLID principles and clean architecture patterns.

## Problems Addressed

### Before Refactoring
```python
class SetFinetuningService:
    def apply(self, message: Message, setter_steps: SetterSteps):
        message.response_finetuning = setter_steps.openai_response.get("response") or []
```

**Issues:**
- **No Type Validation**: Assumed response was always a list
- **Silent Failures**: No error handling for unexpected data types
- **Inconsistent Behavior**: String responses were lost or caused errors
- **No Logging**: No visibility into operation success/failure
- **Violates SRP**: Mixing data access, validation, and assignment

### After Refactoring
```python
class SetFinetuningService:
    def apply(self, message: Message, setter_steps: SetterSteps) -> None:
        # Robust type handling, validation, logging, and error management
```

**Improvements:**
- **Type Safety**: Validates and normalizes different response types
- **Error Handling**: Graceful handling of invalid data with fallbacks
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Single Responsibility**: Clear separation of concerns
- **Documentation**: Complete docstrings and type hints

## Architecture Compliance

### SOLID Principles Applied

#### 1. Single Responsibility Principle (SRP)
- **Main Method**: Coordinates the finetuning application process
- **Normalization Method**: Handles type conversion logic
- **Validation Method**: Validates and converts list elements
- **Each method has one clear responsibility**

#### 2. Open/Closed Principle (OCP)
- **Extensible**: New response types can be added to normalization logic
- **Closed for Modification**: Core logic doesn't need changes for new types

#### 3. Dependency Inversion Principle (DIP)
- **Depends on Abstractions**: Uses domain entities (Message, SetterSteps)
- **Infrastructure Independent**: No direct dependencies on external services

### Clean Architecture Compliance
- **Application Layer Service**: Properly positioned in application layer
- **Domain Entity Usage**: Works with domain entities without modifying their structure
- **No External Dependencies**: Pure business logic without infrastructure concerns

## Key Features

### 1. Type Normalization
```python
def _normalize_response_to_list(self, response_data: Any) -> List[str]:
    """Normalize response data to a list of strings"""
```

**Supported Types:**
- `None` → `[]` (empty list)
- `str` → `[str]` (single element list)
- `list` → validates and converts elements
- `int/float/bool` → `[str(value)]` (converts to string)

**Benefits:**
- **Consistent Output**: Always returns `List[str]`
- **Type Safety**: Validates input types before processing
- **Flexible Input**: Handles various OpenAI response formats

### 2. Robust List Validation
```python
def _validate_and_convert_list(self, response_list: List[Any]) -> List[str]:
    """Validate and convert list elements to strings"""
```

**Features:**
- **Element-by-Element Validation**: Checks each list item
- **Type Conversion**: Converts supported types to strings
- **None Filtering**: Automatically skips None values
- **Detailed Error Messages**: Specifies which element failed and why

### 3. Comprehensive Error Handling
```python
try:
    # Main processing logic
except Exception as e:
    # Detailed error logging
    # Fallback to empty list
    # Re-raise exception for upstream handling
```

**Error Handling Strategy:**
- **Logging**: Captures detailed error context
- **Fallback**: Sets empty list to maintain data consistency
- **Re-raising**: Allows upstream error handling
- **Context Preservation**: Includes message ID and response data in logs

### 4. Structured Logging
```python
logger.info(
    "Finetuning response applied successfully",
    extra={
        "message_id": getattr(message, 'id', 'unknown'),
        "response_type": type(response_data).__name__,
        "response_length": len(normalized_response)
    }
)
```

**Logging Features:**
- **Structured Data**: JSON-compatible extra fields
- **Operation Context**: Message ID, response type, length
- **Success/Failure Tracking**: Different log levels for different outcomes
- **Debugging Support**: Detailed information for troubleshooting

## Usage Examples

### Example 1: String Response
```python
# Input
setter_steps.openai_response = {"response": "This is a finetuning response"}

# Processing
service.apply(message, setter_steps)

# Result
message.response_finetuning = ["This is a finetuning response"]
```

### Example 2: List Response
```python
# Input
setter_steps.openai_response = {"response": ["response1", "response2", "response3"]}

# Processing
service.apply(message, setter_steps)

# Result
message.response_finetuning = ["response1", "response2", "response3"]
```

### Example 3: Mixed Type List
```python
# Input
setter_steps.openai_response = {"response": ["text", 123, True, None, 45.6]}

# Processing
service.apply(message, setter_steps)

# Result
message.response_finetuning = ["text", "123", "True", "45.6"]
# Note: None values are filtered out
```

### Example 4: Error Handling
```python
# Input
setter_steps.openai_response = {"response": {"invalid": "dict"}}

# Processing
try:
    service.apply(message, setter_steps)
except ValueError as e:
    # Error: "Unsupported response data type: dict. Expected str, list, int, float, or bool."
    pass

# Result
message.response_finetuning = []  # Fallback to empty list
```

## Testing Strategy

### Unit Tests Coverage
- **Type Validation**: Tests for all supported and unsupported types
- **Edge Cases**: Empty strings, None values, whitespace-only strings
- **Error Handling**: Verification of exception raising and fallback behavior
- **List Processing**: Mixed type lists, empty lists, invalid elements
- **Logging**: Verification of log messages and context

### Test Categories
1. **Happy Path Tests**: Normal operation with expected data types
2. **Edge Case Tests**: Boundary conditions and special values
3. **Error Tests**: Invalid data types and malformed inputs
4. **Integration Tests**: End-to-end service behavior

## Performance Considerations

### Efficiency Features
- **Early Returns**: Quick processing for None and empty values
- **Type Checking**: Fast isinstance() checks before processing
- **Minimal Allocations**: Efficient list building
- **Logging Optimization**: Conditional logging with lazy evaluation

### Scalability
- **Memory Efficient**: No unnecessary data copying
- **Linear Complexity**: O(n) processing for lists
- **Stateless Design**: No instance state, safe for concurrent use

## Migration Guide

### For Existing Code
No changes required to calling code:
```python
# This continues to work exactly the same
service = SetFinetuningService()
service.apply(message, setter_steps)
```

### Benefits for Existing Usage
- **More Robust**: Handles edge cases that might have caused issues
- **Better Logging**: Improved visibility into operations
- **Type Safety**: Prevents runtime errors from unexpected data types

## Future Enhancements

### Planned Improvements
1. **Configuration Support**: Configurable type conversion rules
2. **Async Support**: Async version for high-throughput scenarios
3. **Validation Rules**: Custom validation logic for specific use cases
4. **Metrics Collection**: Performance and usage metrics

### Extension Points
- **Custom Converters**: Plugin system for custom type conversions
- **Validation Hooks**: Pre/post processing hooks
- **Format Handlers**: Support for additional response formats

## Related Documentation

- See `.github/instructions/architecture-rules.instructions.md` for architecture principles
- See `.github/instructions/openai-client-refactoring.md` for related OpenAI refactoring
- See `tests/unit/test_set_finetuning_service.py` for comprehensive test examples

## Compliance Verification

### SOLID Principles ✅
- [x] Single Responsibility: Each method has one clear purpose
- [x] Open/Closed: Extensible for new types without modification
- [x] Liskov Substitution: Consistent interface behavior
- [x] Interface Segregation: Focused public interface
- [x] Dependency Inversion: Depends on domain abstractions

### Clean Architecture ✅
- [x] Application Layer Service: Properly positioned
- [x] Domain Entity Usage: Works with domain objects
- [x] Infrastructure Independence: No external dependencies
- [x] Business Logic Focus: Pure application logic

### Best Practices ✅
- [x] Error Handling: Comprehensive exception management
- [x] Logging: Structured logging with context
- [x] Documentation: Complete docstrings and type hints
- [x] Testing: Comprehensive unit test coverage
- [x] Type Safety: Full type hints and validation
