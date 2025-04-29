import {
  AgentEvent,
  RunAgentInputInternal,
  ResumeAgentInputInternal,
  ReplayAgentInputInternal,
  ForkAgentInputInternal
} from './types';

function parseSSEMessage<TAgentState, TInterruptValue>(chunk: string): AgentEvent<TAgentState, TInterruptValue>[] {
  const messages: AgentEvent<TAgentState, TInterruptValue>[] = [];
  const lines = chunk.split('\n');
  let currentMessage: Partial<AgentEvent<TAgentState, TInterruptValue>> = {};

  for (const line of lines) {
    if (!line.trim()) {
      if (Object.keys(currentMessage).length) {
        messages.push(currentMessage as AgentEvent<TAgentState, TInterruptValue>);
        currentMessage = {};
      }
      continue;
    }

    const [field, ...valueArr] = line.split(':');
    const value = valueArr.join(':').trim();
    switch (field) {
      case 'event':
        currentMessage.event = value;
        break;
      case 'data':
        currentMessage.data = JSON.parse(value);
        break;
    }
  }

  if (Object.keys(currentMessage).length) {
    messages.push(currentMessage as AgentEvent<TAgentState, TInterruptValue>);
  }

  return messages;
}

export async function* callAgentRoute<TAgentState, TInterruptValue, TResumeValue>(
  body: RunAgentInputInternal<TAgentState> | ResumeAgentInputInternal<TResumeValue> | ForkAgentInputInternal<TAgentState> | ReplayAgentInputInternal):
  AsyncGenerator<AgentEvent<TAgentState, TInterruptValue>, void, unknown> {
  try {
    const response = await fetch('/api/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to call agent route');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No reader available');

    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      console.log("Chunk => ", chunk)

      const parsedMessages = parseSSEMessage<TAgentState, TInterruptValue>(chunk);
      for (const msg of parsedMessages) {
        yield msg;
      }
    }
  } catch (error) {
    console.error('Error in callAgentRoute.', error);
    throw error;
  }
} 

// let buffer = "";

//     while (true) {
//       const { done, value } = await reader.read();
//       if (done) break;
//       buffer += decoder.decode(value, { stream: true });

//       let parts = buffer.split("\n\n");
//       buffer = parts.pop() ?? ""; // Remaining partial message

//       const chunk = decoder.decode(value);

//       for (const part of parts) {
//         const parsedMessages = parseSSEMessage<TAgentState, TInterruptValue>(
//           part,
//         );
//         for (const msg of parsedMessages) {
//           yield msg;
//         }
//       }
//     }
// function parseSSEMessage<TAgentState, TInterruptValue>(chunk: string): AgentEvent<TAgentState, TInterruptValue>[] {
//   const messages: AgentEvent<TAgentState, TInterruptValue>[] = [];
//   const lines = chunk.split("\n");
//   let currentMessage: Partial<AgentEvent<TAgentState, TInterruptValue>> = {};

//   console.log("1) Lines:", lines);

//   for (let rawLine of lines) {
//     // 1. Strip carriage returns + leading `data: ` label
//     const line = rawLine.replace(/^data:\s?/, "").trim();


//     if (!line) {
//       // Finish current message if we hit an empty line
//       if (Object.keys(currentMessage).length) {
//         messages.push(
//           currentMessage as AgentEvent<TAgentState, TInterruptValue>,
//         );
//         currentMessage = {};
//       }
//       continue;
//     }

//     const [field, ...valueArr] = line.split(':');
//     const value = valueArr.join(':').trim();
//     console.log("2) Value to be parsed: ", valueArr);
//     console.log("3) Event: ", field);
//     switch (field) {
//       case 'event':
//         currentMessage.event = value;
//         break;
//       case 'data':
//         try {
//           currentMessage.data = JSON.parse(value);
//         } catch (err) {
//           console.warn("⚠️ JSON.parse failed for chunk:", value);
//           console.warn("Error:", err);
//           // Skip this message, reset state and continue safely
//           currentMessage = {};
//         }
//         break;
//     }
//   }

//   if (Object.keys(currentMessage).length) {
//     messages.push(currentMessage as AgentEvent<TAgentState, TInterruptValue>);
//   }

//   return messages;
// }

// export async function* callAgentRoute<TAgentState, TInterruptValue, TResumeValue>(
//   body: RunAgentInputInternal<TAgentState> | ResumeAgentInputInternal<TResumeValue> | ForkAgentInputInternal<TAgentState> | ReplayAgentInputInternal):
//   AsyncGenerator<AgentEvent<TAgentState, TInterruptValue>, void, unknown> {
//   try {
//     const response = await fetch('/api/agent', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//         "x-tenant-id": "f436cc35-e7af-411d-b4b0-63d3ee183523",
//       },
//       body: JSON.stringify(body),
//     });

//     if (!response.ok) {
//       const error = await response.json();
//       throw new Error(error.detail || 'Failed to call agent route');
//     }

//     const reader = response.body?.getReader();
//     if (!reader) throw new Error('No reader available');

//     const decoder = new TextDecoder();

//     while (true) {
//       const { done, value } = await reader.read();
//       if (done) break;

//       const chunk = decoder.decode(value);
//       const parsedMessages = parseSSEMessage<TAgentState, TInterruptValue>(chunk);

//       for (const msg of parsedMessages) {
//         yield msg;
//       }
//     }
//   } catch (error) {
//     console.error('Error in callAgentRoute.', error);
//     throw error;
//   }
// } 