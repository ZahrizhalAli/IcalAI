'use server';

import { Checkpoint } from './types';

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL;

export async function getHistory<TAgentState, TInterruptValue>(threadId: string): Promise<Checkpoint<TAgentState, TInterruptValue>[]> {
  const response = await fetch(`${AGENT_URL}/history?thread_id=${threadId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "x-tenant-id": "f436cc35-e7af-411d-b4b0-63d3ee183523",
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch agenthistory');
  }

  const data = await response.json();
  return data as Checkpoint<TAgentState, TInterruptValue>[];
}

export async function stopAgent(threadId: string): Promise<void> {
  const response = await fetch(`${AGENT_URL}/agent/stop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "x-tenant-id": "f436cc35-e7af-411d-b4b0-63d3ee183523",
    },
    body: JSON.stringify({ thread_id: threadId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop agent');
  }
}