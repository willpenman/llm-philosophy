# OpenAI Provider Notes

- API: Responses (`POST https://api.openai.com/v1/responses`)
- Auth: `OPENAI_API_KEY`
- Docs: https://platform.openai.com/docs/api-reference/responses (blocked in this environment by Cloudflare)

## Models
- Note that not all models appear consistently in the pricing on the docs
  - e.g. gpt-4o is listed on the pricing page as: gpt-4o ($2.50/$10), and gpt-4o-2024-05-13 ($5/$15). So there's clearly a difference due to price. The unmarked one probably points to gpt-4o-2024-11-20, and there's another one in the pricing that's only listed under fine-tuning, gpt-4o-2024-08-16 (which in the Models part is surprisingly marked as 'default')
- 5.2
- 5.1
- 5
- 5 mini
- 5 nano
- 5.2 Codex
- 5.1 Codex
- 5.1 Codex Max
- 5 Codex
- 5.2 Pro
- 5 Pro
- o3 pro
- o3
- o4 mini
- 4.1 nano
- o1 pro
- 4.5 preview (deprecated)
- o3 mini
- o1
- o1 mini (deprecated)
- o1 preview (deprecated)
- 4o
- 4o mini
- 4 turbo
- 5.2
- babbage 002 (deprecated)
- 4o
- 5.1 Codex mini
- 3.5 turbo
  - gpt-3.5-turbo-instruct (shutdown 9/28/26)
  - gpt-3.5-turbo-1106 (shutdown 9/28/26)
- 4
  - gpt-4-1106-preview (shutdown 3/26/26)
  - gpt-4-0613
  - gpt-4-0314 (shutdown 3/26/26)
  - gpt-4-0125 (i.e. 4 turbo preview - deprecated, shuts down 3/26/26)
- oss-120b
- oss-20b

(excludes 'chat' models like 5.2 Chat, and various other TTS, image gen, realtime audio, embedding etc. models)

## Model parameter availability
- Source: pasted Responses API docs below plus live call results.
- Constraints: `max_output_tokens` is required for any call, and must be >= 16.
- o3-2025-04-16:
  - Supported: `system`/`user` input items, `max_output_tokens`, `reasoning` (`effort`, `summary`), `tools`, `tool_choice`, `seed`, `stream`, `stream_options` (per docs and live-verified).
  - Not supported: `temperature`, `top_p` (live call returns 400 unsupported parameter).
  - Max output upper bound is not reliably enforced in live calls (100001 and 1000001 both succeeded); trust docs for the effective limit.
  - Reasoning effort values:
    - Live: `low`, `medium`, `high` accepted; others (e.g. `ultra`) rejected - 400 unsupported.
  - Error shape observed for invalid `max_output_tokens` (below minimum): HTTP 400, `invalid_request_error`, `param: max_output_tokens`, `code: integer_below_min_value`.
- Debugging note: a `--debug-sse` run records raw SSE event JSONL (event objects such as `response.completed` and `response.reasoning_text.done`) under `tmp/` without writing to request/response JSONL storage.
- Streaming note: when SSE includes reasoning summary deltas (e.g. `response.reasoning_summary_text.delta`), the runner stores a concatenated summary inside the response payload reasoning item (`output[].type=reasoning`), preferring `*.done` content and falling back to joined deltas, using `\n\n\n` between parts.
- gpt-5.2-2025-12-11:
  - Supported: `system`/`user` input items, `max_output_tokens`, `reasoning` (`effort`, `summary`), `tools`, `tool_choice`, `seed`, `stream`, `stream_options`.
  - Not supported: `temperature` (live call returns 400 unsupported parameter).
  - Unverified: `top_p`.
  - Defaults: `max_output_tokens=128000`.
- gpt-4o-2024-05-13:
  - Supported: `system`/`user` input items, `max_output_tokens`, `temperature`, `top_p` (docs and live confirmation).
  - Not supported: `reasoning` (docs and live confirmation).
  - Constraints: `max_output_tokens` upper bound expected 64k output (per docs; unconfirmed).
- TODO: determine if `max_output_tokens` ever outputs an error for being too high; if so, what is the error point for o3 (and how does it relate to the 'true' max tokens, which are recorded as 100k by OAI).

## Reasoning effort defaults (docs excerpt)
- Supported values: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.
- gpt-5.1 defaults to `none` (no reasoning). Supported values for gpt-5.1: `none`, `low`, `medium`, `high`. Tool calls supported for all reasoning values in gpt-5.1.
- All models before gpt-5.1 default to `medium` reasoning effort, and do not support `none`.
- gpt-5-pro defaults to (and only supports) `high` reasoning effort.
- `xhigh` is supported for all models after gpt-5.1-codex-max.

## Pricing schedule (draft)
- Prices are tracked per million tokens for input/output only (other tiers not yet modeled).
- o3-2025-04-16: input $2.00 / output $8.00 per million tokens.
- gpt-4o-2024-05-13: input $2.50 / output $10.00 per million tokens.
- gpt-5.2-2025-12-11: input $1.75 / output $14.00 per million tokens.

## Docs pasted in lieu of direct access
Request body
background
boolean
Optional
Defaults to false
Whether to run the model response in the background. Learn more.
conversation
string or object
Optional
Defaults to null
The conversation that this response belongs to. Items from this conversation are prepended to input_items for this response request. Input items and output items from this response are automatically added to this conversation after this response completes.

Hide possible types
Conversation ID
string
The unique ID of the conversation.
Conversation object
object
The conversation that this response belongs to.

Hide properties
id
string
Required
The unique ID of the conversation.
include
array
Optional
Specify additional output data to include in the model response. Currently supported values are:

web_search_call.action.sources: Include the sources of the web search tool call.
code_interpreter_call.outputs: Includes the outputs of python code execution in code interpreter tool call items.
computer_call_output.output.image_url: Include image urls from the computer call output.
file_search_call.results: Include the search results of the file search tool call.
message.input_image.image_url: Include image urls from the input message.
message.output_text.logprobs: Include logprobs with assistant messages.
reasoning.encrypted_content: Includes an encrypted version of reasoning tokens in reasoning item outputs. This enables reasoning items to be used in multi-turn conversations when using the Responses API statelessly (like when the store parameter is set to false, or when an organization is enrolled in the zero data retention program).
input
string or array
Optional
Text, image, or file inputs to the model, used to generate a response.

Learn more:

Text inputs and outputs
Image inputs
File inputs
Conversation state
Function calling

Hide possible types
Text input
string
A text input to the model, equivalent to a text input with the user role.
Input item list
array
A list of one or many input items to the model, containing different content types.

Hide possible types
Input message
object
A message input to the model with a role indicating instruction following hierarchy. Instructions given with the developer or system role take precedence over instructions given with the user role. Messages with the assistant role are presumed to have been generated by the model in previous interactions.

Hide properties
content
string or array
Required
Text, image, or audio input to the model, used to generate a response. Can also contain previous assistant responses.

Hide possible types
Text input
string
A text input to the model.
Input item content list
array
A list of one or many input items to the model, containing different content types.

Hide possible types
Input text
object
A text input to the model.

Hide properties
text
string
Required
The text input to the model.
type
string
Required
The type of the input item. Always input_text.
Input image
object
An image input to the model. Learn about image inputs.

Hide properties
detail
string
Required
The detail level of the image to be sent to the model. One of high, low, or auto. Defaults to auto.
type
string
Required
The type of the input item. Always input_image.
file_id
string
Optional
The ID of the file to be sent to the model.
image_url
string
Optional
The URL of the image to be sent to the model. A fully qualified URL or base64 encoded image in a data URL.
Input file
object
A file input to the model.

Hide properties
type
string
Required
The type of the input item. Always input_file.
file_data
string
Optional
The content of the file to be sent to the model.
file_id
string
Optional
The ID of the file to be sent to the model.
file_url
string
Optional
The URL of the file to be sent to the model.
filename
string
Optional
The name of the file to be sent to the model.
role
string
Required
The role of the message input. One of user, assistant, system, or developer.
type
string
Optional
The type of the message input. Always message.
Item
object
An item representing part of the context for the response to be generated by the model. Can contain text, images, and audio inputs, as well as previous assistant responses and tool call outputs.

Hide possible types
Input message
object
A message input to the model with a role indicating instruction following hierarchy. Instructions given with the developer or system role take precedence over instructions given with the user role.

Hide properties
content
array
Required
A list of one or many input items to the model, containing different content types.

Hide possible types
Input text
object
A text input to the model.

Hide properties
text
string
Required
The text input to the model.
type
string
Required
The type of the input item. Always input_text.
Input image
object
An image input to the model. Learn about image inputs.

Hide properties
detail
string
Required
The detail level of the image to be sent to the model. One of high, low, or auto. Defaults to auto.
type
string
Required
The type of the input item. Always input_image.
file_id
string
Optional
The ID of the file to be sent to the model.
image_url
string
Optional
The URL of the image to be sent to the model. A fully qualified URL or base64 encoded image in a data URL.
Input file
object
A file input to the model.

Hide properties
type
string
Required
The type of the input item. Always input_file.
file_data
string
Optional
The content of the file to be sent to the model.
file_id
string
Optional
The ID of the file to be sent to the model.
file_url
string
Optional
The URL of the file to be sent to the model.
filename
string
Optional
The name of the file to be sent to the model.
role
string
Required
The role of the message input. One of user, system, or developer.
status
string
Optional
The status of item. One of in_progress, completed, or incomplete. Populated when items are returned via API.
type
string
Optional
The type of the message input. Always set to message.
Output message
object
An output message from the model.

Hide properties
content
array
Required
The content of the output message.

Hide possible types
Output text
object
A text output from the model.

Hide properties
annotations
array
Required
The annotations of the text output.

Hide possible types
File citation
object
A citation to a file.

Hide properties
file_id
string
Required
The ID of the file.
filename
string
Required
The filename of the file cited.
index
integer
Required
The index of the file in the list of files.
type
string
Required
The type of the file citation. Always file_citation.
URL citation
object
A citation for a web resource used to generate a model response.

Hide properties
end_index
integer
Required
The index of the last character of the URL citation in the message.
start_index
integer
Required
The index of the first character of the URL citation in the message.
title
string
Required
The title of the web resource.
type
string
Required
The type of the URL citation. Always url_citation.
url
string
Required
The URL of the web resource.
Container file citation
object
A citation for a container file used to generate a model response.

Hide properties
container_id
string
Required
The ID of the container file.
end_index
integer
Required
The index of the last character of the container file citation in the message.
file_id
string
Required
The ID of the file.
filename
string
Required
The filename of the container file cited.
start_index
integer
Required
The index of the first character of the container file citation in the message.
type
string
Required
The type of the container file citation. Always container_file_citation.
File path
object
A path to a file.

Hide properties
file_id
string
Required
The ID of the file.
index
integer
Required
The index of the file in the list of files.
type
string
Required
The type of the file path. Always file_path.
logprobs
array
Required

Hide properties
bytes
array
Required
logprob
number
Required
token
string
Required
top_logprobs
array
Required

Hide properties
bytes
array
Required
logprob
number
Required
token
string
Required
text
string
Required
The text output from the model.
type
string
Required
The type of the output text. Always output_text.
Refusal
object
A refusal from the model.

Hide properties
refusal
string
Required
The refusal explanation from the model.
type
string
Required
The type of the refusal. Always refusal.
id
string
Required
The unique ID of the output message.
role
string
Required
The role of the output message. Always assistant.
status
string
Required
The status of the message input. One of in_progress, completed, or incomplete. Populated when input items are returned via API.
type
string
Required
The type of the output message. Always message.
File search tool call
object
The results of a file search tool call. See the file search guide for more information.

Hide properties
id
string
Required
The unique ID of the file search tool call.
queries
array
Required
The queries used to search for files.
status
string
Required
The status of the file search tool call. One of in_progress, searching, incomplete or failed,
type
string
Required
The type of the file search tool call. Always file_search_call.
results
array
Optional
The results of the file search tool call.

Hide properties
attributes
map
Optional
Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.
file_id
string
Optional
The unique ID of the file.
filename
string
Optional
The name of the file.
score
number
Optional
The relevance score of the file - a value between 0 and 1.
text
string
Optional
The text that was retrieved from the file.
Computer tool call
object
A tool call to a computer use tool. See the computer use guide for more information.

Hide properties
action
object
Required

Hide possible types
Click
object
A click action.

Hide properties
button
string
Required
Indicates which mouse button was pressed during the click. One of left, right, wheel, back, or forward.
type
string
Required
Specifies the event type. For a click action, this property is always click.
x
integer
Required
The x-coordinate where the click occurred.
y
integer
Required
The y-coordinate where the click occurred.
DoubleClick
object
A double click action.

Hide properties
type
string
Required
Specifies the event type. For a double click action, this property is always set to double_click.
x
integer
Required
The x-coordinate where the double click occurred.
y
integer
Required
The y-coordinate where the double click occurred.
Drag
object
A drag action.

Hide properties
path
array
Required
An array of coordinates representing the path of the drag action. Coordinates will appear as an array of objects, eg

[
  { x: 100, y: 200 },
  { x: 200, y: 300 }
]

Hide properties
x
integer
Required
The x-coordinate.
y
integer
Required
The y-coordinate.
type
string
Required
Specifies the event type. For a drag action, this property is always set to drag.
KeyPress
object
A collection of keypresses the model would like to perform.

Hide properties
keys
array
Required
The combination of keys the model is requesting to be pressed. This is an array of strings, each representing a key.
type
string
Required
Specifies the event type. For a keypress action, this property is always set to keypress.
Move
object
A mouse move action.

Hide properties
type
string
Required
Specifies the event type. For a move action, this property is always set to move.
x
integer
Required
The x-coordinate to move to.
y
integer
Required
The y-coordinate to move to.
Screenshot
object
A screenshot action.

Hide properties
type
string
Required
Specifies the event type. For a screenshot action, this property is always set to screenshot.
Scroll
object
A scroll action.

Hide properties
scroll_x
integer
Required
The horizontal scroll distance.
scroll_y
integer
Required
The vertical scroll distance.
type
string
Required
Specifies the event type. For a scroll action, this property is always set to scroll.
x
integer
Required
The x-coordinate where the scroll occurred.
y
integer
Required
The y-coordinate where the scroll occurred.
Type
object
An action to type in text.

Hide properties
text
string
Required
The text to type.
type
string
Required
Specifies the event type. For a type action, this property is always set to type.
Wait
object
A wait action.

Hide properties
type
string
Required
Specifies the event type. For a wait action, this property is always set to wait.
call_id
string
Required
An identifier used when responding to the tool call with output.
id
string
Required
The unique ID of the computer call.
pending_safety_checks
array
Required
The pending safety checks for the computer call.

Hide properties
id
string
Required
The ID of the pending safety check.
code
string
Optional
The type of the pending safety check.
message
string
Optional
Details about the pending safety check.
status
string
Required
The status of the item. One of in_progress, completed, or incomplete. Populated when items are returned via API.
type
string
Required
The type of the computer call. Always computer_call.
Computer tool call output
object
The output of a computer tool call.

Hide properties
call_id
string
Required
The ID of the computer tool call that produced the output.
output
object
Required
A computer screenshot image used with the computer use tool.

Hide properties
type
string
Required
Specifies the event type. For a computer screenshot, this property is always set to computer_screenshot.
file_id
string
Optional
The identifier of an uploaded file that contains the screenshot.
image_url
string
Optional
The URL of the screenshot image.
type
string
Required
The type of the computer tool call output. Always computer_call_output.
acknowledged_safety_checks
array
Optional
The safety checks reported by the API that have been acknowledged by the developer.

Hide properties
id
string
Required
The ID of the pending safety check.
code
string
Optional
The type of the pending safety check.
message
string
Optional
Details about the pending safety check.
id
string
Optional
The ID of the computer tool call output.
status
string
Optional
The status of the message input. One of in_progress, completed, or incomplete. Populated when input items are returned via API.
Web search tool call
object
The results of a web search tool call. See the web search guide for more information.

Hide properties
action
object
Required
An object describing the specific action taken in this web search call. Includes details on how the model used the web (search, open_page, find).

Hide possible types
Search action
object
Action type "search" - Performs a web search query.

Hide properties
query
string
Required
[DEPRECATED] The search query.
type
string
Required
The action type.
queries
array
Optional
The search queries.
sources
array
Optional
The sources used in the search.

Hide properties
type
string
Required
The type of source. Always url.
url
string
Required
The URL of the source.
Open page action
object
Action type "open_page" - Opens a specific URL from search results.

Hide properties
type
string
Required
The action type.
url
string
Required
The URL opened by the model.
Find action
object
Action type "find": Searches for a pattern within a loaded page.

Hide properties
pattern
string
Required
The pattern or text to search for within the page.
type
string
Required
The action type.
url
string
Required
The URL of the page searched for the pattern.
id
string
Required
The unique ID of the web search tool call.
status
string
Required
The status of the web search tool call.
type
string
Required
The type of the web search tool call. Always web_search_call.
Function tool call
object
A tool call to run a function. See the function calling guide for more information.

Hide properties
arguments
string
Required
A JSON string of the arguments to pass to the function.
call_id
string
Required
The unique ID of the function tool call generated by the model.
name
string
Required
The name of the function to run.
type
string
Required
The type of the function tool call. Always function_call.
id
string
Optional
The unique ID of the function tool call.
status
string
Optional
The status of the item. One of in_progress, completed, or incomplete. Populated when items are returned via API.
Function tool call output
object
The output of a function tool call.

Hide properties
call_id
string
Required
The unique ID of the function tool call generated by the model.
output
string or array
Required
Text, image, or file output of the function tool call.

Hide possible types
string
A JSON string of the output of the function tool call.
array
An array of content outputs (text, image, file) for the function tool call.

Hide possible types
Input text
object
A text input to the model.

Hide properties
text
string
Required
The text input to the model.
type
string
Required
The type of the input item. Always input_text.
Input image
object
An image input to the model. Learn about image inputs

Hide properties
type
string
Required
The type of the input item. Always input_image.
detail
string
Optional
The detail level of the image to be sent to the model. One of high, low, or auto. Defaults to auto.
file_id
string
Optional
The ID of the file to be sent to the model.
image_url
string
Optional
The URL of the image to be sent to the model. A fully qualified URL or base64 encoded image in a data URL.
Input file
object
A file input to the model.

Hide properties
type
string
Required
The type of the input item. Always input_file.
file_data
string
Optional
The base64-encoded data of the file to be sent to the model.
file_id
string
Optional
The ID of the file to be sent to the model.
file_url
string
Optional
The URL of the file to be sent to the model.
filename
string
Optional
The name of the file to be sent to the model.
type
string
Required
The type of the function tool call output. Always function_call_output.
id
string
Optional
The unique ID of the function tool call output. Populated when this item is returned via API.
status
string
Optional
The status of the item. One of in_progress, completed, or incomplete. Populated when items are returned via API.
Reasoning
object
A description of the chain of thought used by a reasoning model while generating a response. Be sure to include these items in your input to the Responses API for subsequent turns of a conversation if you are manually managing context.

Hide properties
id
string
Required
The unique identifier of the reasoning content.
summary
array
Required
Reasoning summary content.

Hide properties
text
string
Required
A summary of the reasoning output from the model so far.
type
string
Required
The type of the object. Always summary_text.
type
string
Required
The type of the object. Always reasoning.
content
array
Optional
Reasoning text content.

Hide properties
text
string
Required
The reasoning text from the model.
type
string
Required
The type of the reasoning text. Always reasoning_text.
encrypted_content
string
Optional
The encrypted content of the reasoning item - populated when a response is generated with reasoning.encrypted_content in the include parameter.
status
string
Optional
The status of the item. One of in_progress, completed, or incomplete. Populated when items are returned via API.
Compaction item
object
A compaction item generated by the 
v1/responses/compact
API.

Hide properties
encrypted_content
string
Required
The encrypted content of the compaction summary.
type
string
Required
The type of the item. Always compaction.
id
string
Optional
The ID of the compaction item.
Image generation call
object
An image generation request made by the model.

Hide properties
id
string
Required
The unique ID of the image generation call.
result
string
Required
The generated image encoded in base64.
status
string
Required
The status of the image generation call.
type
string
Required
The type of the image generation call. Always image_generation_call.
Code interpreter tool call
object
A tool call to run code.

Hide properties
code
string
Required
The code to run, or null if not available.
container_id
string
Required
The ID of the container used to run the code.
id
string
Required
The unique ID of the code interpreter tool call.
outputs
array
Required
The outputs generated by the code interpreter, such as logs or images. Can be null if no outputs are available.

Hide possible types
Code interpreter output logs
object
The logs output from the code interpreter.

Hide properties
logs
string
Required
The logs output from the code interpreter.
type
string
Required
The type of the output. Always logs.
Code interpreter output image
object
The image output from the code interpreter.

Hide properties
type
string
Required
The type of the output. Always image.
url
string
Required
The URL of the image output from the code interpreter.
status
string
Required
The status of the code interpreter tool call. Valid values are in_progress, completed, incomplete, interpreting, and failed.
type
string
Required
The type of the code interpreter tool call. Always code_interpreter_call.
Local shell call
object
A tool call to run a command on the local shell.

Hide properties
action
object
Required
Execute a shell command on the server.

Hide properties
command
array
Required
The command to run.
env
map
Required
Environment variables to set for the command.
type
string
Required
The type of the local shell action. Always exec.
timeout_ms
integer
Optional
Optional timeout in milliseconds for the command.
user
string
Optional
Optional user to run the command as.
working_directory
string
Optional
Optional working directory to run the command in.
call_id
string
Required
The unique ID of the local shell tool call generated by the model.
id
string
Required
The unique ID of the local shell call.
status
string
Required
The status of the local shell call.
type
string
Required
The type of the local shell call. Always local_shell_call.
Local shell call output
object
The output of a local shell tool call.

Hide properties
id
string
Required
The unique ID of the local shell tool call generated by the model.
output
string
Required
A JSON string of the output of the local shell tool call.
type
string
Required
The type of the local shell tool call output. Always local_shell_call_output.
status
string
Optional
The status of the item. One of in_progress, completed, or incomplete.
Shell tool call
object
A tool representing a request to execute one or more shell commands.

Hide properties
action
object
Required
The shell commands and limits that describe how to run the tool call.

Hide properties
commands
array
Required
Ordered shell commands for the execution environment to run.
max_output_length
integer
Optional
Maximum number of UTF-8 characters to capture from combined stdout and stderr output.
timeout_ms
integer
Optional
Maximum wall-clock time in milliseconds to allow the shell commands to run.
call_id
string
Required
The unique ID of the shell tool call generated by the model.
type
string
Required
The type of the item. Always shell_call.
id
string
Optional
The unique ID of the shell tool call. Populated when this item is returned via API.
status
string
Optional
The status of the shell call. One of in_progress, completed, or incomplete.
Shell tool call output
object
The streamed output items emitted by a shell tool call.

Hide properties
call_id
string
Required
The unique ID of the shell tool call generated by the model.
output
array
Required
Captured chunks of stdout and stderr output, along with their associated outcomes.

Hide properties
outcome
object
Required
The exit or timeout outcome associated with this shell call.

Hide possible types
Shell call timeout outcome
object
Indicates that the shell call exceeded its configured time limit.

Hide properties
type
string
Required
The outcome type. Always timeout.
Shell call exit outcome
object
Indicates that the shell commands finished and returned an exit code.

Hide properties
exit_code
integer
Required
The exit code returned by the shell process.
type
string
Required
The outcome type. Always exit.
stderr
string
Required
Captured stderr output for the shell call.
stdout
string
Required
Captured stdout output for the shell call.
type
string
Required
The type of the item. Always shell_call_output.
id
string
Optional
The unique ID of the shell tool call output. Populated when this item is returned via API.
max_output_length
integer
Optional
The maximum number of UTF-8 characters captured for this shell call's combined output.
Apply patch tool call
object
A tool call representing a request to create, delete, or update files using diff patches.

Hide properties
call_id
string
Required
The unique ID of the apply patch tool call generated by the model.
operation
object
Required
The specific create, delete, or update instruction for the apply_patch tool call.

Hide possible types
Apply patch create file operation
object
Instruction for creating a new file via the apply_patch tool.

Hide properties
diff
string
Required
Unified diff content to apply when creating the file.
path
string
Required
Path of the file to create relative to the workspace root.
type
string
Required
The operation type. Always create_file.
Apply patch delete file operation
object
Instruction for deleting an existing file via the apply_patch tool.

Hide properties
path
string
Required
Path of the file to delete relative to the workspace root.
type
string
Required
The operation type. Always delete_file.
Apply patch update file operation
object
Instruction for updating an existing file via the apply_patch tool.

Hide properties
diff
string
Required
Unified diff content to apply to the existing file.
path
string
Required
Path of the file to update relative to the workspace root.
type
string
Required
The operation type. Always update_file.
status
string
Required
The status of the apply patch tool call. One of in_progress or completed.
type
string
Required
The type of the item. Always apply_patch_call.
id
string
Optional
The unique ID of the apply patch tool call. Populated when this item is returned via API.
Apply patch tool call output
object
The streamed output emitted by an apply patch tool call.

Hide properties
call_id
string
Required
The unique ID of the apply patch tool call generated by the model.
status
string
Required
The status of the apply patch tool call output. One of completed or failed.
type
string
Required
The type of the item. Always apply_patch_call_output.
id
string
Optional
The unique ID of the apply patch tool call output. Populated when this item is returned via API.
output
string
Optional
Optional human-readable log text from the apply patch tool (e.g., patch results or errors).
MCP list tools
object
A list of tools available on an MCP server.

Hide properties
id
string
Required
The unique ID of the list.
server_label
string
Required
The label of the MCP server.
tools
array
Required
The tools available on the server.

Hide properties
input_schema
object
Required
The JSON schema describing the tool's input.
name
string
Required
The name of the tool.
annotations
object
Optional
Additional annotations about the tool.
description
string
Optional
The description of the tool.
type
string
Required
The type of the item. Always mcp_list_tools.
error
string
Optional
Error message if the server could not list tools.
MCP approval request
object
A request for human approval of a tool invocation.

Hide properties
arguments
string
Required
A JSON string of arguments for the tool.
id
string
Required
The unique ID of the approval request.
name
string
Required
The name of the tool to run.
server_label
string
Required
The label of the MCP server making the request.
type
string
Required
The type of the item. Always mcp_approval_request.
MCP approval response
object
A response to an MCP approval request.

Hide properties
approval_request_id
string
Required
The ID of the approval request being answered.
approve
boolean
Required
Whether the request was approved.
type
string
Required
The type of the item. Always mcp_approval_response.
id
string
Optional
The unique ID of the approval response
reason
string
Optional
Optional reason for the decision.
MCP tool call
object
An invocation of a tool on an MCP server.

Hide properties
arguments
string
Required
A JSON string of the arguments passed to the tool.
id
string
Required
The unique ID of the tool call.
name
string
Required
The name of the tool that was run.
server_label
string
Required
The label of the MCP server running the tool.
type
string
Required
The type of the item. Always mcp_call.
approval_request_id
string
Optional
Unique identifier for the MCP tool call approval request. Include this value in a subsequent mcp_approval_response input to approve or reject the corresponding tool call.
error
string
Optional
The error from the tool call, if any.
output
string
Optional
The output from the tool call.
status
string
Optional
The status of the tool call. One of in_progress, completed, incomplete, calling, or failed.
Custom tool call output
object
The output of a custom tool call from your code, being sent back to the model.

Hide properties
call_id
string
Required
The call ID, used to map this custom tool call output to a custom tool call.
output
string or array
Required
The output from the custom tool call generated by your code. Can be a string or an list of output content.

Hide possible types
string output
string
A string of the output of the custom tool call.
output content list
array
Text, image, or file output of the custom tool call.

Hide possible types
Input text
object
A text input to the model.

Hide properties
text
string
Required
The text input to the model.
type
string
Required
The type of the input item. Always input_text.
Input image
object
An image input to the model. Learn about image inputs.

Hide properties
detail
string
Required
The detail level of the image to be sent to the model. One of high, low, or auto. Defaults to auto.
type
string
Required
The type of the input item. Always input_image.
file_id
string
Optional
The ID of the file to be sent to the model.
image_url
string
Optional
The URL of the image to be sent to the model. A fully qualified URL or base64 encoded image in a data URL.
Input file
object
A file input to the model.

Hide properties
type
string
Required
The type of the input item. Always input_file.
file_data
string
Optional
The content of the file to be sent to the model.
file_id
string
Optional
The ID of the file to be sent to the model.
file_url
string
Optional
The URL of the file to be sent to the model.
filename
string
Optional
The name of the file to be sent to the model.
type
string
Required
The type of the custom tool call output. Always custom_tool_call_output.
id
string
Optional
The unique ID of the custom tool call output in the OpenAI platform.
Custom tool call
object
A call to a custom tool created by the model.

Hide properties
call_id
string
Required
An identifier used to map this custom tool call to a tool call output.
input
string
Required
The input for the custom tool call generated by the model.
name
string
Required
The name of the custom tool being called.
type
string
Required
The type of the custom tool call. Always custom_tool_call.
id
string
Optional
The unique ID of the custom tool call in the OpenAI platform.
Item reference
object
An internal identifier for an item to reference.

Hide properties
id
string
Required
The ID of the item to reference.
type
string
Optional
Defaults to item_reference
The type of item to reference. Always item_reference.
instructions
string
Optional
A system (or developer) message inserted into the model's context.

When using along with previous_response_id, the instructions from a previous response will not be carried over to the next response. This makes it simple to swap out system (or developer) messages in new responses.
max_output_tokens
integer
Optional
An upper bound for the number of tokens that can be generated for a response, including visible output tokens and reasoning tokens.
max_tool_calls
integer
Optional
The maximum number of total calls to built-in tools that can be processed in a response. This maximum number applies across all built-in tool calls, not per individual tool. Any further attempts to call a tool by the model will be ignored.
metadata
map
Optional
Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard.

Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.
model
string
Optional
Model ID used to generate the response, like gpt-4o or o3. OpenAI offers a wide range of models with different capabilities, performance characteristics, and price points. Refer to the model guide to browse and compare available models.
parallel_tool_calls
boolean
Optional
Defaults to true
Whether to allow the model to run tool calls in parallel.
previous_response_id
string
Optional
The unique ID of the previous response to the model. Use this to create multi-turn conversations. Learn more about conversation state. Cannot be used in conjunction with conversation.
prompt
object
Optional
Reference to a prompt template and its variables. Learn more.

Hide properties
id
string
Required
The unique identifier of the prompt template to use.
variables
map
Optional
Optional map of values to substitute in for variables in your prompt. The substitution values can either be strings, or other Response input types like images or files.
version
string
Optional
Optional version of the prompt template.
prompt_cache_key
string
Optional
Used by OpenAI to cache responses for similar requests to optimize your cache hit rates. Replaces the user field. Learn more.
prompt_cache_retention
string
Optional
The retention policy for the prompt cache. Set to 24h to enable extended prompt caching, which keeps cached prefixes active for longer, up to a maximum of 24 hours. Learn more.
reasoning
object
Optional
gpt-5 and o-series models only

Configuration options for reasoning models.

Hide properties
effort
string
Optional
Defaults to medium
Constrains effort on reasoning for reasoning models. Currently supported values are none, minimal, low, medium, high, and xhigh. Reducing reasoning effort can result in faster responses and fewer tokens used on reasoning in a response.

gpt-5.1 defaults to none, which does not perform reasoning. The supported reasoning values for gpt-5.1 are none, low, medium, and high. Tool calls are supported for all reasoning values in gpt-5.1.
All models before gpt-5.1 default to medium reasoning effort, and do not support none.
The gpt-5-pro model defaults to (and only supports) high reasoning effort.
xhigh is supported for all models after gpt-5.1-codex-max.
generate_summary
Deprecated
string
Optional
Deprecated: use summary instead.

A summary of the reasoning performed by the model. This can be useful for debugging and understanding the model's reasoning process. One of auto, concise, or detailed.
summary
string
Optional
A summary of the reasoning performed by the model. This can be useful for debugging and understanding the model's reasoning process. One of auto, concise, or detailed.

concise is supported for computer-use-preview models and all reasoning models after gpt-5.
safety_identifier
string
Optional
A stable identifier used to help detect users of your application that may be violating OpenAI's usage policies. The IDs should be a string that uniquely identifies each user. We recommend hashing their username or email address, in order to avoid sending us any identifying information. Learn more.
service_tier
string
Optional
Defaults to auto
Specifies the processing type used for serving the request.

If set to 'auto', then the request will be processed with the service tier configured in the Project settings. Unless otherwise configured, the Project will use 'default'.
If set to 'default', then the request will be processed with the standard pricing and performance for the selected model.
If set to 'flex' or 'priority', then the request will be processed with the corresponding service tier.
When not set, the default behavior is 'auto'.
When the service_tier parameter is set, the response body will include the service_tier value based on the processing mode actually used to serve the request. This response value may be different from the value set in the parameter.
store
boolean
Optional
Defaults to true
Whether to store the generated model response for later retrieval via API.
stream
boolean
Optional
Defaults to false
If set to true, the model response data will be streamed to the client as it is generated using server-sent events. See the Streaming section below for more information.
stream_options
object
Optional
Defaults to null
Options for streaming responses. Only set this when you set stream: true.

Hide properties
include_obfuscation
boolean
Optional
When true, stream obfuscation will be enabled. Stream obfuscation adds random characters to an obfuscation field on streaming delta events to normalize payload sizes as a mitigation to certain side-channel attacks. These obfuscation fields are included by default, but add a small amount of overhead to the data stream. You can set include_obfuscation to false to optimize for bandwidth if you trust the network links between your application and the OpenAI API.
temperature
number
Optional
Defaults to 1
What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. We generally recommend altering this or top_p but not both.
text
object
Optional
Configuration options for a text response from the model. Can be plain text or structured JSON data. Learn more:

Text inputs and outputs
Structured Outputs

Hide properties
format
object
Optional
An object specifying the format that the model must output.

Configuring { "type": "json_schema" } enables Structured Outputs, which ensures the model will match your supplied JSON schema. Learn more in the Structured Outputs guide.

The default format is { "type": "text" } with no additional options.

Not recommended for gpt-4o and newer models:

Setting to { "type": "json_object" } enables the older JSON mode, which ensures the message the model generates is valid JSON. Using json_schema is preferred for models that support it.

Hide possible types
Text
object
Default response format. Used to generate text responses.

Hide properties
type
string
Required
The type of response format being defined. Always text.
JSON schema
object
JSON Schema response format. Used to generate structured JSON responses. Learn more about Structured Outputs.

Hide properties
name
string
Required
The name of the response format. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.
schema
object
Required
The schema for the response format, described as a JSON Schema object. Learn how to build JSON schemas here.
type
string
Required
The type of response format being defined. Always json_schema.
description
string
Optional
A description of what the response format is for, used by the model to determine how to respond in the format.
strict
boolean
Optional
Defaults to false
Whether to enable strict schema adherence when generating the output. If set to true, the model will always follow the exact schema defined in the schema field. Only a subset of JSON Schema is supported when strict is true. To learn more, read the Structured Outputs guide.
JSON object
object
JSON object response format. An older method of generating JSON responses. Using json_schema is recommended for models that support it. Note that the model will not generate JSON without a system or user message instructing it to do so.

Hide properties
type
string
Required
The type of response format being defined. Always json_object.
verbosity
string
Optional
Defaults to medium
Constrains the verbosity of the model's response. Lower values will result in more concise responses, while higher values will result in more verbose responses. Currently supported values are low, medium, and high.
tool_choice
string or object
Optional
How the model should select which tool (or tools) to use when generating a response. See the tools parameter to see how to specify which tools the model can call.

Hide possible types
Tool choice mode
string
Controls which (if any) tool is called by the model.

none means the model will not call any tool and instead generates a message.

auto means the model can pick between generating a message or calling one or more tools.

required means the model must call one or more tools.
Allowed tools
object
Constrains the tools available to the model to a pre-defined set.

Hide properties
mode
string
Required
Constrains the tools available to the model to a pre-defined set.

auto allows the model to pick from among the allowed tools and generate a message.

required requires the model to call one or more of the allowed tools.
tools
array
Required
A list of tool definitions that the model should be allowed to call.

For the Responses API, the list of tool definitions might look like:

[
  { "type": "function", "name": "get_weather" },
  { "type": "mcp", "server_label": "deepwiki" },
  { "type": "image_generation" }
]

Hide properties
type
string
Required
Allowed tool configuration type. Always allowed_tools.
Hosted tool
object
Indicates that the model should use a built-in tool to generate a response. Learn more about built-in tools.

Hide properties
type
string
Required
The type of hosted tool the model should to use. Learn more about built-in tools.

Allowed values are:

file_search
web_search_preview
computer_use_preview
code_interpreter
image_generation
Function tool
object
Use this option to force the model to call a specific function.

Hide properties
name
string
Required
The name of the function to call.
type
string
Required
For function calling, the type is always function.
MCP tool
object
Use this option to force the model to call a specific tool on a remote MCP server.

Hide properties
server_label
string
Required
The label of the MCP server to use.
type
string
Required
For MCP tools, the type is always mcp.
name
string
Optional
The name of the tool to call on the server.
Custom tool
object
Use this option to force the model to call a specific custom tool.

Hide properties
name
string
Required
The name of the custom tool to call.
type
string
Required
For custom tool calling, the type is always custom.
Specific apply patch tool choice
object
Forces the model to call the apply_patch tool when executing a tool call.

Hide properties
type
string
Required
The tool to call. Always apply_patch.
Specific shell tool choice
object
Forces the model to call the shell tool when a tool call is required.

Hide properties
type
string
Required
The tool to call. Always shell.
tools
array
Optional
An array of tools the model may call while generating a response. You can specify which tool to use by setting the tool_choice parameter.

We support the following categories of tools:

Built-in tools: Tools that are provided by OpenAI that extend the model's capabilities, like web search or file search. Learn more about built-in tools.
MCP Tools: Integrations with third-party systems via custom MCP servers or predefined connectors such as Google Drive and SharePoint. Learn more about MCP Tools.
Function calls (custom tools): Functions that are defined by you, enabling the model to call your own code with strongly typed arguments and outputs. Learn more about function calling. You can also use custom tools to call your own code.

Hide possible types
Function
object
Defines a function in your own code the model can choose to call. Learn more about function calling.

Hide properties
name
string
Required
The name of the function to call.
parameters
map
Required
A JSON schema object describing the parameters of the function.
strict
boolean
Required
Whether to enforce strict parameter validation. Default true.
type
string
Required
The type of the function tool. Always function.
description
string
Optional
A description of the function. Used by the model to determine whether or not to call the function.
File search
object
A tool that searches for relevant content from uploaded files. Learn more about the file search tool.

Hide properties
type
string
Required
The type of the file search tool. Always file_search.
vector_store_ids
array
Required
The IDs of the vector stores to search.
filters
object
Optional
A filter to apply.

Hide possible types
Comparison Filter
object
A filter used to compare a specified attribute key to a given value using a defined comparison operation.

Hide properties
key
string
Required
The key to compare against the value.
type
string
Required
Specifies the comparison operator: eq, ne, gt, gte, lt, lte, in, nin.

eq: equals
ne: not equal
gt: greater than
gte: greater than or equal
lt: less than
lte: less than or equal
in: in
nin: not in
value
string / number / boolean / array
Required
The value to compare against the attribute key; supports string, number, or boolean types.
Compound Filter
object
Combine multiple filters using and or or.

Hide properties
filters
array
Required
Array of filters to combine. Items can be ComparisonFilter or CompoundFilter.

Hide possible types
Comparison Filter
object
A filter used to compare a specified attribute key to a given value using a defined comparison operation.

Hide properties
key
string
Required
The key to compare against the value.
type
string
Required
Specifies the comparison operator: eq, ne, gt, gte, lt, lte, in, nin.

eq: equals
ne: not equal
gt: greater than
gte: greater than or equal
lt: less than
lte: less than or equal
in: in
nin: not in
value
string / number / boolean / array
Required
The value to compare against the attribute key; supports string, number, or boolean types.
type
string
Required
Type of operation: and or or.
max_num_results
integer
Optional
The maximum number of results to return. This number should be between 1 and 50 inclusive.
ranking_options
object
Optional
Ranking options for search.

Hide properties
hybrid_search
object
Optional
Weights that control how reciprocal rank fusion balances semantic embedding matches versus sparse keyword matches when hybrid search is enabled.

Hide properties
embedding_weight
number
Required
The weight of the embedding in the reciprocal ranking fusion.
text_weight
number
Required
The weight of the text in the reciprocal ranking fusion.
ranker
string
Optional
The ranker to use for the file search.
score_threshold
number
Optional
The score threshold for the file search, a number between 0 and 1. Numbers closer to 1 will attempt to return only the most relevant results, but may return fewer results.
Computer use preview
object
A tool that controls a virtual computer. Learn more about the computer tool.

Hide properties
display_height
integer
Required
The height of the computer display.
display_width
integer
Required
The width of the computer display.
environment
string
Required
The type of computer environment to control.
type
string
Required
The type of the computer use tool. Always computer_use_preview.
Web search
object
Search the Internet for sources related to the prompt. Learn more about the web search tool.

Hide properties
type
string
Required
The type of the web search tool. One of web_search or web_search_2025_08_26.
filters
object
Optional
Filters for the search.

Hide properties
allowed_domains
array
Optional
Defaults to []
Allowed domains for the search. If not provided, all domains are allowed. Subdomains of the provided domains are allowed as well.

Example: ["pubmed.ncbi.nlm.nih.gov"]
search_context_size
string
Optional
Defaults to medium
High level guidance for the amount of context window space to use for the search. One of low, medium, or high. medium is the default.
user_location
object
Optional
The approximate location of the user.

Hide properties
city
string
Optional
Free text input for the city of the user, e.g. San Francisco.
country
string
Optional
The two-letter ISO country code of the user, e.g. US.
region
string
Optional
Free text input for the region of the user, e.g. California.
timezone
string
Optional
The IANA timezone of the user, e.g. America/Los_Angeles.
type
string
Optional
Defaults to approximate
The type of location approximation. Always approximate.
MCP tool
object
Give the model access to additional tools via remote Model Context Protocol (MCP) servers. Learn more about MCP.

Hide properties
server_label
string
Required
A label for this MCP server, used to identify it in tool calls.
type
string
Required
The type of the MCP tool. Always mcp.
allowed_tools
array or object
Optional
List of allowed tool names or a filter object.

Hide possible types
MCP allowed tools
array
A string array of allowed tool names
MCP tool filter
object
A filter object to specify which tools are allowed.

Hide properties
read_only
boolean
Optional
Indicates whether or not a tool modifies data or is read-only. If an MCP server is annotated with
readOnlyHint
, it will match this filter.
tool_names
array
Optional
List of allowed tool names.
authorization
string
Optional
An OAuth access token that can be used with a remote MCP server, either with a custom MCP server URL or a service connector. Your application must handle the OAuth authorization flow and provide the token here.
connector_id
string
Optional
Identifier for service connectors, like those available in ChatGPT. One of server_url or connector_id must be provided. Learn more about service connectors here.

Currently supported connector_id values are:

Dropbox: connector_dropbox
Gmail: connector_gmail
Google Calendar: connector_googlecalendar
Google Drive: connector_googledrive
Microsoft Teams: connector_microsoftteams
Outlook Calendar: connector_outlookcalendar
Outlook Email: connector_outlookemail
SharePoint: connector_sharepoint
headers
object
Optional
Optional HTTP headers to send to the MCP server. Use for authentication or other purposes.
require_approval
object or string
Optional
Defaults to always
Specify which of the MCP server's tools require approval.

Hide possible types
MCP tool approval filter
object
Specify which of the MCP server's tools require approval. Can be always, never, or a filter object associated with tools that require approval.

Hide properties
always
object
Optional
A filter object to specify which tools are allowed.

Hide properties
read_only
boolean
Optional
Indicates whether or not a tool modifies data or is read-only. If an MCP server is annotated with
readOnlyHint
, it will match this filter.
tool_names
array
Optional
List of allowed tool names.
never
object
Optional
A filter object to specify which tools are allowed.

Hide properties
read_only
boolean
Optional
Indicates whether or not a tool modifies data or is read-only. If an MCP server is annotated with
readOnlyHint
, it will match this filter.
tool_names
array
Optional
List of allowed tool names.
MCP tool approval setting
string
Specify a single approval policy for all tools. One of always or never. When set to always, all tools will require approval. When set to never, all tools will not require approval.
server_description
string
Optional
Optional description of the MCP server, used to provide more context.
server_url
string
Optional
The URL for the MCP server. One of server_url or connector_id must be provided.
Code interpreter
object
A tool that runs Python code to help generate a response to a prompt.

Hide properties
container
string or object
Required
The code interpreter container. Can be a container ID or an object that specifies uploaded file IDs to make available to your code, along with an optional memory_limit setting.

Hide possible types
string
The container ID.
CodeInterpreterToolAuto
object
Configuration for a code interpreter container. Optionally specify the IDs of the files to run the code on.

Hide properties
type
string
Required
Always auto.
file_ids
array
Optional
An optional list of uploaded files to make available to your code.
memory_limit
string
Optional
The memory limit for the code interpreter container.
type
string
Required
The type of the code interpreter tool. Always code_interpreter.
Image generation tool
object
A tool that generates images using the GPT image models.

Hide properties
type
string
Required
The type of the image generation tool. Always image_generation.
background
string
Optional
Defaults to auto
Background type for the generated image. One of transparent, opaque, or auto. Default: auto.
input_fidelity
string
Optional
Control how much effort the model will exert to match the style and features, especially facial features, of input images. This parameter is only supported for gpt-image-1. Unsupported for gpt-image-1-mini. Supports high and low. Defaults to low.
input_image_mask
object
Optional
Optional mask for inpainting. Contains image_url (string, optional) and file_id (string, optional).

Hide properties
file_id
string
Optional
File ID for the mask image.
image_url
string
Optional
Base64-encoded mask image.
model
string
Optional
moderation
string
Optional
Defaults to auto
Moderation level for the generated image. Default: auto.
output_compression
integer
Optional
Defaults to 100
Compression level for the output image. Default: 100.
output_format
string
Optional
Defaults to png
The output format of the generated image. One of png, webp, or jpeg. Default: png.
partial_images
integer
Optional
Defaults to 0
Number of partial images to generate in streaming mode, from 0 (default value) to 3.
quality
string
Optional
Defaults to auto
The quality of the generated image. One of low, medium, high, or auto. Default: auto.
size
string
Optional
Defaults to auto
The size of the generated image. One of 1024x1024, 1024x1536, 1536x1024, or auto. Default: auto.
Local shell tool
object
A tool that allows the model to execute shell commands in a local environment.

Hide properties
type
string
Required
The type of the local shell tool. Always local_shell.
Shell tool
object
A tool that allows the model to execute shell commands.

Hide properties
type
string
Required
The type of the shell tool. Always shell.
Custom tool
object
A custom tool that processes input using a specified format. Learn more about custom tools

Hide properties
name
string
Required
The name of the custom tool, used to identify it in tool calls.
type
string
Required
The type of the custom tool. Always custom.
description
string
Optional
Optional description of the custom tool, used to provide more context.
format
object
Optional
The input format for the custom tool. Default is unconstrained text.

Hide possible types
Text format
object
Unconstrained free-form text.

Hide properties
type
string
Required
Unconstrained text format. Always text.
Grammar format
object
A grammar defined by the user.

Hide properties
definition
string
Required
The grammar definition.
syntax
string
Required
The syntax of the grammar definition. One of lark or regex.
type
string
Required
Grammar format. Always grammar.
Web search preview
object
This tool searches the web for relevant results to use in a response. Learn more about the web search tool.

Hide properties
type
string
Required
The type of the web search tool. One of web_search_preview or web_search_preview_2025_03_11.
search_context_size
string
Optional
High level guidance for the amount of context window space to use for the search. One of low, medium, or high. medium is the default.
user_location
object
Optional
The user's location.

Hide properties
type
string
Required
The type of location approximation. Always approximate.
city
string
Optional
Free text input for the city of the user, e.g. San Francisco.
country
string
Optional
The two-letter ISO country code of the user, e.g. US.
region
string
Optional
Free text input for the region of the user, e.g. California.
timezone
string
Optional
The IANA timezone of the user, e.g. America/Los_Angeles.
Apply patch tool
object
Allows the assistant to create, delete, or update files using unified diffs.

Hide properties
type
string
Required
The type of the tool. Always apply_patch.
top_logprobs
integer
Optional
An integer between 0 and 20 specifying the number of most likely tokens to return at each token position, each with an associated log probability.
top_p
number
Optional
Defaults to 1
An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.

We generally recommend altering this or temperature but not both.
truncation
string
Optional
Defaults to disabled
The truncation strategy to use for the model response.

auto: If the input to this Response exceeds the model's context window size, the model will truncate the response to fit the context window by dropping items from the beginning of the conversation.
disabled (default): If the input size will exceed the context window size for a model, the request will fail with a 400 error.
user
Deprecated
string
Optional
This field is being replaced by safety_identifier and prompt_cache_key. Use prompt_cache_key instead to maintain caching optimizations. A stable identifier for your end-users. Used to boost cache hit rates by better bucketing similar requests and to help OpenAI detect and prevent abuse. Learn more.
Returns
Returns a Response object.
