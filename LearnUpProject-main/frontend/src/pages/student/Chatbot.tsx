import { useEffect, useRef, useState } from "react";
import * as chatApi from "../../services/chat";
import { getApiErrorMessage } from "../../services/api";

const INTRO_TEXT =
  "Hello! I'm your University Assistant. How can I help you with advising, policies, or your wellbeing today?";

/** Same vibe as Chatbot/index.html: dark glass dashboard, indigo accent, Outfit feel */
export default function ChatbotPage() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<chatApi.ChatMessageRow[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [pendingUser, setPendingUser] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, pendingUser]);

  const ensureSession = async () => {
    if (sessionId != null) return sessionId;
    const s = await chatApi.startChatSession();
    setSessionId(s.session_id);
    return s.session_id;
  };

  const loadMessages = async (sid: number) => {
    const list = await chatApi.getChatMessages(sid);
    setMessages(list);
  };

  const startFresh = async () => {
    setErr("");
    setPendingUser(null);
    try {
      const s = await chatApi.startChatSession();
      setSessionId(s.session_id);
      setMessages([]);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const sessions = await chatApi.getMyChatSessions();
        if (sessions.length > 0) {
          const latest = sessions[0];
          setSessionId(latest.id);
          await loadMessages(latest.id);
        }
      } catch {
        /* optional */
      }
    })();
  }, []);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setErr("");
    setInput("");
    setPendingUser(text);
    setLoading(true);
    try {
      const sid = await ensureSession();
      await chatApi.sendChatMessage(sid, text);
      setSessionId(sid);
      await loadMessages(sid);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setPendingUser(null);
      setLoading(false);
    }
  };

  const showIntro = messages.length === 0 && !pendingUser && !loading;

  return (
    <div className="min-h-[calc(100vh-6rem)] flex flex-col">
      <div className="mb-4">
        <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">Graduation Assistant</h1>
        <p className="text-sm text-slate-500 mt-1">
          Same AI engine as your standalone Chatbot — RAG over advising, registration, policies, and wellbeing.
        </p>
      </div>

      <div
        className="flex-1 flex flex-col rounded-3xl overflow-hidden border border-white/10 min-h-[520px] max-h-[min(78vh,760px)]
        bg-slate-900/95 backdrop-blur-xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.45)]"
        style={{
          backgroundImage:
            "radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,0.25) 0, transparent 50%)",
        }}
      >
        <header className="shrink-0 px-5 py-5 border-b border-white/10 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-100 font-display tracking-tight">Graduation Assistant</h2>
          <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" aria-hidden />
            AI engine
          </div>
        </header>

        <div
          id="chat-scroll"
          className="flex-1 overflow-y-auto px-5 py-5 flex flex-col gap-4"
          style={{ scrollbarWidth: "thin" }}
        >
          {showIntro ? (
            <div className="message-animate self-start max-w-[85%] rounded-2xl px-[18px] py-3 text-[15px] leading-relaxed bg-white/[0.08] border border-white/10 text-slate-200 rounded-bl-md">
              {INTRO_TEXT}
            </div>
          ) : null}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`message-animate max-w-[85%] rounded-2xl px-[18px] py-3 text-[15px] leading-relaxed ${
                m.sender_type === "user"
                  ? "self-end bg-indigo-500 text-white rounded-br-md shadow-lg shadow-indigo-900/30"
                  : "self-start bg-white/[0.08] border border-white/10 text-slate-200 rounded-bl-md"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.message_text}</p>
              <p className="text-[10px] mt-2 opacity-60">
                {new Date(m.created_at).toLocaleTimeString()}
              </p>
            </div>
          ))}

          {pendingUser ? (
            <div className="message-animate self-end max-w-[85%] rounded-2xl px-[18px] py-3 text-[15px] bg-indigo-500 text-white rounded-br-md">
              {pendingUser}
            </div>
          ) : null}

          {loading ? (
            <div className="message-animate self-start max-w-[85%] rounded-2xl px-[18px] py-3 text-[15px] bg-white/[0.08] border border-white/10 text-slate-300 rounded-bl-md italic">
              Analyzing…
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>

        {err ? (
          <div className="px-5 py-2 text-sm text-amber-200 bg-red-950/40 border-t border-white/10">{err}</div>
        ) : null}

        <div className="shrink-0 px-5 py-5 border-t border-white/10 flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), void send())}
            placeholder="Ask me about GPA rules, stress, or registration…"
            disabled={loading}
            className="flex-1 rounded-xl bg-black/20 border border-white/10 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-indigo-400 transition-colors disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => void send()}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-semibold px-6 py-3 text-sm transition-colors disabled:opacity-40 disabled:pointer-events-none"
          >
            Send
          </button>
          <button
            type="button"
            onClick={() => void startFresh()}
            className="rounded-xl border border-white/15 text-slate-300 text-xs font-semibold px-3 py-2 hover:bg-white/5"
          >
            New chat
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .message-animate { animation: fadeInUp 0.3s ease-out; }
      `}</style>
    </div>
  );
}
