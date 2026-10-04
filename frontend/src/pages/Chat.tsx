import { FormEvent, useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Bot, CircleStop, LoaderCircle, RotateCcw, ShieldCheck, UserRound } from "lucide-react";
import { toast } from "sonner";
import type { ChatReply, Source } from "../api";
import { sendChat } from "../api";
import type { useSangyanState } from "../state";
import { Markdown } from "../components/Markdown";
import { SourceCards } from "../components/SourceCards";
import { PageHeading } from "../components/PageHeading";
import { Button } from "../components/ui/button";

type Props = ReturnType<typeof useSangyanState>;
type ChatItem = { id: string; role: "user" | "assistant"; content: string; sources?: Source[]; mode?: string };
const CHAT_KEY = "sangyan.chat";
const PENDING_FIELD_KEY = "sangyan.pending-case-field";

function getChatHistory(): ChatItem[] {
  try { return JSON.parse(localStorage.getItem(CHAT_KEY) ?? "[]") as ChatItem[]; } catch { return []; }
}

export function ChatPage({ caseData, setCaseData, language, sessionId }: Props) {
  const [messages, setMessages] = useState<ChatItem[]>(getChatHistory);
  const [draft, setDraft] = useState("");
  const [pendingField, setPendingField] = useState<string | null>(
    () => localStorage.getItem(PENDING_FIELD_KEY),
  );
  const [showScrollButton, setShowScrollButton] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const mutation = useMutation({
    mutationFn: sendChat,
    onSuccess: (reply: ChatReply) => {
      const answer: ChatItem = { id: crypto.randomUUID(), role: "assistant", content: reply.answer, sources: reply.sources };
      setMessages((current) => {
        const next = [...current, answer];
        localStorage.setItem(CHAT_KEY, JSON.stringify(next));
        return next;
      });
      if (reply.case) setCaseData(reply.case);
      setPendingField(reply.pending_case_field);
      if (reply.pending_case_field) localStorage.setItem(PENDING_FIELD_KEY, reply.pending_case_field);
      else localStorage.removeItem(PENDING_FIELD_KEY);
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Your message could not be sent."),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, mutation.isPending]);

  function handleScroll() {
    const node = scrollRef.current;
    if (node) setShowScrollButton(node.scrollHeight - node.scrollTop - node.clientHeight > 220);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || mutation.isPending) return;
    const userMessage: ChatItem = { id: crypto.randomUUID(), role: "user", content: text };
    const next = [...messages, userMessage];
    setMessages(next);
    localStorage.setItem(CHAT_KEY, JSON.stringify(next));
    setDraft("");
    mutation.mutate({
      session_id: sessionId,
      message: text,
      history: messages.map(({ role, content }) => ({ role, content })),
      language,
      case: caseData,
      pending_case_field: pendingField,
    });
  }

  function clearChat() {
    setMessages([]);
    setPendingField(null);
    localStorage.removeItem(CHAT_KEY);
    localStorage.removeItem(PENDING_FIELD_KEY);
    toast.success("Conversation cleared from this device.");
  }

  return (
    <div className="content-page chat-page">
      <PageHeading eyebrow="YOUR INVESTOR SUPPORT" title="Ask Sangyan" description="Share what’s on your mind. For procedural questions, we’ll check official sources before guiding you." action={<button className="button button-quiet" onClick={clearChat}><RotateCcw size={15} /> New chat</button>} />
      <section className="chat-card">
        <div className="chat-topline"><div className="assistant-identity"><span className="assistant-avatar"><Bot size={19} /></span><span><b>Sangyan Sahayak</b><small>Investor Protection Assistant</small></span></div><div className="chat-live"><i /> Ready to help</div></div>
        <div className="chat-transcript" ref={scrollRef} onScroll={handleScroll} aria-live="polite">
          {messages.length === 0 ? (
            <div className="chat-welcome"><div className="welcome-bot"><Bot size={28} /></div><h2>Namaste. What can I help you with?</h2><p>Ask a question, or tell me what happened. We can take it one step at a time.</p><div className="prompt-chips"><button onClick={() => setDraft("I have a question about my demat account")}>Demat account question</button><button onClick={() => setDraft("I need help with an investor grievance")}>Help with a grievance</button><button onClick={() => setDraft("How do I raise a complaint through SCORES?")}>SCORES process</button></div></div>
          ) : messages.map((message) => (
            <article className={`message-row ${message.role}`} key={message.id}>
              <span className={`message-avatar ${message.role}`}>{message.role === "assistant" ? <Bot size={16} /> : <UserRound size={16} />}</span>
              <div className="message-content"><div className="message-label">{message.role === "assistant" ? "Sangyan" : "You"}</div><Markdown content={message.content} />{message.role === "assistant" && message.sources?.length ? <SourceCards sources={message.sources} /> : null}</div>
            </article>
          ))}
          {mutation.isPending && <div className="message-row assistant"><span className="message-avatar assistant"><Bot size={16} /></span><div className="typing-indicator"><LoaderCircle size={15} className="spin" />{pendingField ? "Checking official sources…" : "Thinking…"}</div></div>}
          {mutation.isError && <div className="chat-error"><CircleStop size={16} /> The service couldn’t complete that message. Your conversation is still saved here; please try again.</div>}
          <div ref={bottomRef} />
        </div>
        {showScrollButton && <button className="scroll-bottom" onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })} aria-label="Scroll to latest message"><ArrowDown size={16} /></button>}
        <form className="chat-composer" onSubmit={submit}>
          <textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="Aap apna sawaal Hinglish, Hindi ya English mein likh sakte hain…" rows={2} disabled={mutation.isPending} aria-label="Your message" />
          <div className="composer-bottom"><span><ShieldCheck size={13} /> Regulatory answers are grounded in official sources</span><Button type="submit" size="icon" disabled={!draft.trim() || mutation.isPending} aria-label="Send message"><ArrowUp size={18} /></Button></div>
        </form>
      </section>
      <p className="chat-footnote">Avoid sharing passwords, OTPs, full account numbers, or other sensitive credentials.</p>
    </div>
  );
}
