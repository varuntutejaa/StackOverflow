"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Loader2, Mic, Send, Volume2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge, Progress } from "@/components/ui/misc";
import { apiFetch } from "@/lib/api";
import { useInterview, useSubmitTurn } from "@/lib/hooks";
import type { Interview } from "@/lib/types";
import { cn, titleCase } from "@/lib/utils";

interface Props {
  interviewId: string;
  onComplete?: (interview: Interview) => void;
  compact?: boolean;
}

// Web Speech API typing (best-effort)
type AnySpeech = any;

export function InterviewConsole({ interviewId, onComplete, compact }: Props) {
  const { data: interview, refetch } = useInterview(interviewId);
  const submitTurn = useSubmitTurn(interviewId);
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [ttsOn, setTtsOn] = useState(true);
  const recognitionRef = useRef<AnySpeech>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const completedRef = useRef(false);

  const messages = interview?.messages ?? [];
  const done = interview?.status === "completed";

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  useEffect(() => {
    if (done && !completedRef.current) {
      completedRef.current = true;
      onComplete?.(interview!);
    }
  }, [done, interview, onComplete]);

  // speak assistant message
  useEffect(() => {
    if (!ttsOn || !messages.length) return;
    const last = messages[messages.length - 1];
    if (last.role !== "assistant" || !last.text_original) return;
    try {
      const u = new SpeechSynthesisUtterance(last.text_original);
      u.lang = { hi: "hi-IN", en: "en-IN", sat: "hi-IN", hoc: "hi-IN", unr: "hi-IN" }[last.language] || "hi-IN";
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch {
      /* not supported */
    }
  }, [messages, ttsOn]);

  const lang = interview?.language ?? "hi";

  async function send(payloadText: string) {
    if (!payloadText.trim() || done) return;
    setText("");
    try {
      // translate to English via backend for non-English so extraction is accurate
      let english: string | undefined;
      if (lang !== "en") {
        try {
          const r = await apiFetch<{ text_english: string }>("/voice/transcribe", {
            method: "POST",
            body: {
              audio_base64: btoa(unescape(encodeURIComponent(JSON.stringify({ text: payloadText })))),
              language: lang,
            },
          });
          english = r.text_english;
        } catch {
          /* fall through */
        }
      }
      const res = await submitTurn.mutateAsync({ text: payloadText, text_english: english, language: lang });
      if (res.is_complete) toast.success("Interview complete — profile extracted");
      refetch();
    } catch {
      toast.error("Could not submit answer");
    }
  }

  function toggleMic() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      toast.info("Voice input not supported in this browser — type the answer instead.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const rec: AnySpeech = new SR();
    rec.lang = { hi: "hi-IN", en: "en-IN" }[lang] || "hi-IN";
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setText(transcript);
      setListening(false);
      send(transcript);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
    setListening(true);
  }

  return (
    <Card className={compact ? "" : "h-full"}>
      <CardHeader className="flex-row items-center justify-between border-b border-border">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Bot className="size-4 text-primary" /> Kaushal AI Voice Interview
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Language: {titleCase(lang)} · STT/LLM: {interview?.stt_provider ?? "mock"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={done ? "success" : "warning"}>{titleCase(interview?.status ?? "loading")}</Badge>
          <Button variant="ghost" size="icon" onClick={() => setTtsOn((v) => !v)} aria-label="Toggle voice output">
            <Volume2 className={cn("size-4", ttsOn ? "text-primary" : "text-muted-foreground")} />
          </Button>
        </div>
      </CardHeader>

      <div className="px-5 pt-3">
        <Progress value={interview?.completion_pct ?? 0} />
        <p className="mt-1 text-right text-xs text-muted-foreground">{Math.round(interview?.completion_pct ?? 0)}% complete</p>
      </div>

      <CardContent className="pt-3">
        <div ref={scrollRef} className={cn("space-y-3 overflow-y-auto pr-1", compact ? "max-h-[320px]" : "max-h-[46vh]")}>
          {messages.map((m) => (
            <div key={m.id} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-3.5 py-2 text-sm",
                  m.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground",
                )}
              >
                <p>{m.text_original}</p>
                {m.text_english && m.text_english !== m.text_original && (
                  <p className={cn("mt-1 text-xs", m.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground")}>
                    ↳ {m.text_english}
                  </p>
                )}
              </div>
            </div>
          ))}
          {submitTurn.isPending && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="size-3 animate-spin" /> Kaushal AI is responding…
            </div>
          )}
        </div>

        {!done && (
          <form
            className="mt-4 flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
            }}
          >
            <Button type="button" variant={listening ? "destructive" : "outline"} size="icon" onClick={toggleMic}>
              <Mic className="size-4" />
            </Button>
            <Input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={listening ? "Listening…" : "Speak or type the beneficiary's answer…"}
              disabled={submitTurn.isPending}
            />
            <Button type="submit" size="icon" loading={submitTurn.isPending}>
              <Send className="size-4" />
            </Button>
          </form>
        )}

        {done && interview?.structured_profile && (
          <div className="mt-4 rounded-lg border border-success/30 bg-success/5 p-3 text-sm">
            <p className="font-semibold text-success">Structured profile extracted</p>
            <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {Object.entries(interview.structured_profile)
                .filter(([k]) => !["source"].includes(k))
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <span className="text-muted-foreground">{titleCase(k)}</span>
                    <span className="text-right font-medium">{Array.isArray(v) ? v.join(", ") || "—" : String(v ?? "—")}</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
