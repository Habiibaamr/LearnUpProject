import { api } from "./api";

export interface ChatStartResponse {
  session_id: number;
  started_at: string;
}

export interface ChatSourceItem {
  id?: string | null;
  title?: string | null;
}

export interface ChatMessageResponse {
  session_id: number;
  user_message: string;
  assistant_response: string;
  kb?: string | null;
  sources?: ChatSourceItem[];
}

export interface ChatMessageRow {
  id: number;
  session_id: number;
  sender_type: string;
  message_text: string;
  created_at: string;
}

export interface ChatSessionRow {
  id: number;
  user_id: number;
  started_at: string;
  ended_at: string | null;
}

export async function startChatSession() {
  const { data } = await api.post<ChatStartResponse>("/chat/start");
  return data;
}

export async function sendChatMessage(sessionId: number, message: string) {
  const { data } = await api.post<ChatMessageResponse>(`/chat/${sessionId}/message`, {
    message,
  });
  return data;
}

export async function getChatMessages(sessionId: number) {
  const { data } = await api.get<ChatMessageRow[]>(`/chat/${sessionId}/messages`);
  return data;
}

export async function getMyChatSessions() {
  const { data } = await api.get<ChatSessionRow[]>("/chat/my-sessions");
  return data;
}
