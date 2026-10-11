
"use client";

import { DragEvent, FormEvent, useMemo, useState } from "react";

const tones = ["tierno", "absurdo", "caótico"] as const;

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const [tone, setTone] = useState<string>("");

  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const previewUrl = useMemo(() => {
    if (!file) return null;
    return URL.createObjectURL(file);
  }, [file]);

  function selectFile(selectedFile?: File) {
    if (!selectedFile) return;

    const allowedTypes = [
      "video/mp4",
      "video/quicktime",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      alert("Solo se permiten videos MP4 o MOV.");
      return;
    }

    if (selectedFile.size > 100 * 1024 * 1024) {
      alert("El video no puede superar 100 MB.");
      return;
    }

    setFile(selectedFile);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();

    selectFile(event.dataTransfer.files?.[0]);
  }

  async function pollJob(jobId: string, apiUrl: string) {
    while (true) {
      const response = await fetch(`${apiUrl}/jobs/${jobId}`);
  
      if (!response.ok) {
        throw new Error(
          `Error consultando job: ${response.status}`
        );
      }
  
      const job = await response.json();
  
      console.log("Estado:", job.status);
  
      setJobStatus(job.status);
  
      if (job.status === "DONE") {
        setIsProcessing(false);
        console.log("Resultado final:", job);
        return job;
      }
  
      if (job.status === "FAILED") {
        setIsProcessing(false);
        throw new Error("El procesamiento del video falló.");
      }
  
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
  
    if (!file) {
      alert("Selecciona un video.");
      return;
    }
  
    if (!prompt.trim()) {
      alert("Escribe qué quieres lograr.");
      return;
    }
  
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
    if (!apiUrl) {
      alert("Falta configurar NEXT_PUBLIC_API_URL.");
      return;
    }
    setIsProcessing(true);
    setJobStatus("PENDING_UPLOAD");
  
    try {
      const response = await fetch(`${apiUrl}/jobs`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          prompt:
            tone.length > 0
              ? `${prompt.trim()}. Tono deseado: ${tone}.`
              : prompt.trim(),
          contentType: file.type,
        }),
      });
  
      if (!response.ok) {
        throw new Error(
          `Error creando job: ${response.status}`
        );
      }
  
      const data = await response.json();

      const uploadResponse = await fetch(data.uploadUrl, {
        method: "PUT",
        headers: {
          "Content-Type": file.type,
        },
        body: file,
      });
      
      if (!uploadResponse.ok) {
        throw new Error(
          `Error subiendo video: ${uploadResponse.status}`
        );
      }
      
      console.log("Video subido correctamente");
      await pollJob(data.jobId, apiUrl);
  
      alert(`Job creado: ${data.jobId}`);
    } catch (error) {
      console.error(error);
      setIsProcessing(false);
      alert("No se pudo completar el análisis.");
    }
  }
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#151515] text-[#F5F5F5]">
      {/* Atmosphere */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_12%_-8%,rgba(183,243,74,0.1),transparent_55%),radial-gradient(ellipse_55%_40%_at_92%_8%,rgba(246,200,76,0.08),transparent_50%)]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-5 py-7 sm:px-8 sm:py-10 lg:px-10">
        {/* Header */}
        <header className="mb-10 flex items-end justify-between gap-4 sm:mb-14">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#B7F34A]">
              Funny Videos
            </p>
            <p className="mt-1 text-sm text-[#B3B3B3]">
              AI comedy assistant
            </p>
          </div>

          <span className="rounded-full border border-[rgba(255,255,255,0.12)] bg-[#1E1E1E] px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-[#B7F34A]">
            PoC
          </span>
        </header>

        {/* Hero */}
        <section className="mb-8 max-w-3xl sm:mb-10">
          <h1 className="text-[2.1rem] font-black leading-[1.05] tracking-[-0.04em] text-[#F5F5F5] sm:text-5xl">
            Encuentra la idea graciosa{" "}
            <span className="bg-gradient-to-r from-[#B7F34A] via-[#D4F06A] to-[#F6C84C] bg-clip-text text-transparent">
              escondida en tu video.
            </span>
          </h1>

          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[#B3B3B3] sm:text-base">
            Sube un clip corto. Analizamos los mejores momentos y
            proponemos guion, memes, música y texto para publicarlo.
          </p>
        </section>

        <form
          onSubmit={handleSubmit}
          className="grid flex-1 gap-5 lg:grid-cols-[0.95fr_1.05fr] lg:gap-6"
        >
          {/* VIDEO */}
          <section className="group relative flex flex-col overflow-hidden rounded-[1.75rem] border border-[rgba(255,255,255,0.12)] bg-[#1E1E1E] p-3 shadow-[0_18px_50px_-28px_rgba(0,0,0,0.55)] sm:p-4">
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#B7F34A]/50 to-transparent"
            />

            {previewUrl ? (
              <>
                <div className="relative overflow-hidden rounded-[1.25rem] bg-[#151515] ring-1 ring-[rgba(255,255,255,0.12)]">
                  <div
                    aria-hidden
                    className="pointer-events-none absolute left-3 top-3 z-10 rounded-full border border-[rgba(255,255,255,0.12)] bg-[#1E1E1E]/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-[#B7F34A] backdrop-blur-md"
                  >
                    Preview
                  </div>
                  <video
                    src={previewUrl}
                    controls
                    className="aspect-[9/12] max-h-[520px] w-full object-contain"
                  />
                </div>

                <div className="mt-4 flex items-center justify-between gap-4 px-1">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-[#F5F5F5]">
                      {file?.name}
                    </p>

                    <p className="mt-0.5 text-xs text-[#B3B3B3]">
                      {file &&
                        (file.size / 1024 / 1024).toFixed(2)}{" "}
                      MB
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="shrink-0 rounded-full border border-[rgba(255,255,255,0.12)] bg-[#252525] px-4 py-2 text-sm text-[#F5F5F5] transition hover:border-[#F6C84C]/50 hover:bg-[#F6C84C]/10 hover:text-[#F6C84C]"
                  >
                    Cambiar
                  </button>
                </div>
              </>
            ) : (
              <div
                onDragOver={(event) => event.preventDefault()}
                onDrop={handleDrop}
                className="relative flex min-h-[420px] flex-1 flex-col items-center justify-center rounded-[1.25rem] border border-dashed border-[rgba(255,255,255,0.22)] bg-[#252525] p-8 text-center transition duration-300 hover:border-[#B7F34A]/70 hover:bg-[#2A2A2A] sm:min-h-[460px]"
              >
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-[rgba(183,243,74,0.35)] bg-[rgba(183,243,74,0.12)] text-[#B7F34A] shadow-[0_0_36px_-10px_rgba(183,243,74,0.55)] transition duration-300 group-hover:scale-105">
                  <svg
                    aria-hidden
                    viewBox="0 0 24 24"
                    className="h-7 w-7"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.75"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 16V4m0 0 4 4m-4-4-4 4"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M4 16.5V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1.5"
                    />
                  </svg>
                </div>

                <h2 className="text-xl font-bold tracking-tight text-[#F5F5F5] sm:text-2xl">
                  Suelta un video corto
                </h2>

                <p className="mt-2 text-sm text-[#B3B3B3]">
                  MP4 o MOV · máximo 100 MB
                </p>

                <p className="mt-1 text-xs text-[#B3B3B3]/80">
                  Idealmente menos de 30 segundos
                </p>

                <label className="mt-8 cursor-pointer rounded-full bg-[#F5F5F5] px-6 py-2.5 text-sm font-semibold text-[#151515] shadow-[0_8px_24px_-12px_rgba(255,255,255,0.35)] transition hover:bg-[#B7F34A] active:scale-[0.98]">
                  Elegir video

                  <input
                    type="file"
                    accept="video/mp4,video/quicktime"
                    className="hidden"
                    onChange={(event) => {
                      selectFile(event.target.files?.[0]);
                    }}
                  />
                </label>
              </div>
            )}
          </section>

          {/* PROMPT */}
          <section className="relative flex flex-col overflow-hidden rounded-[1.75rem] border border-[rgba(255,255,255,0.12)] bg-[#1E1E1E] p-5 shadow-[0_18px_50px_-28px_rgba(0,0,0,0.55)] sm:p-7 lg:p-8">
            <div
              aria-hidden
              className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[rgba(246,200,76,0.08)] blur-3xl"
            />

            <div className="relative">
              <span className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#B3B3B3]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#B7F34A] shadow-[0_0_8px_rgba(183,243,74,0.8)]" />
                Describe la idea
              </span>

              <h2 className="mt-3 text-2xl font-bold tracking-tight text-[#F5F5F5] sm:text-[1.75rem]">
                ¿Qué quieres lograr?
              </h2>

              <p className="mt-2 max-w-md text-sm leading-relaxed text-[#B3B3B3]">
                No necesitas explicar cómo editarlo. Solo dinos qué
                resultado buscas.
              </p>
            </div>

            <div className="relative mt-7">
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Ej. Hazlo gracioso, como si estuviera luchando por no quedarse dormido..."
                rows={7}
                maxLength={500}
                className="w-full resize-none rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#252525] p-5 text-[15px] leading-relaxed text-[#F5F5F5] outline-none transition placeholder:text-[#B3B3B3]/70 focus:border-[#B7F34A]/55 focus:shadow-[0_0_0_3px_rgba(183,243,74,0.14)]"
              />

              <div className="mt-2 text-right text-[11px] tabular-nums text-[#B3B3B3]">
                {prompt.length}/500
              </div>
            </div>

            <div className="mt-5">
              <p className="mb-3 text-xs font-medium uppercase tracking-[0.16em] text-[#B3B3B3]">
                Tono opcional
              </p>

              <div className="flex flex-wrap gap-2">
                {tones.map((item) => {
                  const active = tone === item;

                  return (
                    <button
                      type="button"
                      key={item}
                      onClick={() =>
                        setTone(active ? "" : item)
                      }
                      className={`rounded-full px-4 py-2 text-sm capitalize transition duration-200 ${
                        active
                          ? "bg-gradient-to-r from-[#B7F34A] to-[#F6C84C] font-semibold text-[#151515] shadow-[0_8px_24px_-10px_rgba(183,243,74,0.55)]"
                          : "border border-[rgba(255,255,255,0.12)] bg-[#252525] text-[#F5F5F5] hover:border-[#B7F34A]/40 hover:text-[#B7F34A]"
                      }`}
                    >
                      {item}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="relative mt-auto pt-8">
              <button
                type="submit"
                disabled={!file || !prompt.trim() || isProcessing}
                className="group/cta relative w-full overflow-hidden rounded-2xl bg-gradient-to-r from-[#B7F34A] via-[#C8F25A] to-[#F6C84C] px-5 py-4 text-[15px] font-bold tracking-tight text-[#151515] shadow-[0_14px_36px_-14px_rgba(183,243,74,0.55)] transition duration-200 hover:brightness-105 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-none disabled:bg-[#252525] disabled:text-[#B3B3B3] disabled:shadow-none disabled:brightness-100"
              >
                <span className="relative z-10 inline-flex items-center justify-center gap-2">
                  {isProcessing ? "Analizando..." : "Analizar video"}

                  {!isProcessing && (
                    <span
                      aria-hidden
                      className="transition-transform duration-200 group-hover/cta:translate-x-0.5 group-disabled/cta:translate-x-0"
                    >
                      →
                    </span>
                  )}
                </span>
              </button>

              {jobStatus && (
                <div className="mt-4 text-center text-sm text-[#B7F34A]">
                  {jobStatus === "PENDING_UPLOAD" && "Subiendo video..."}
                  {jobStatus === "ANALYZING" && "Analizando humor..."}
                  {jobStatus === "SEARCHING" && "Buscando memes y música..."}
                  {jobStatus === "WRITING" && "Preparando resultado..."}
                  {jobStatus === "DONE" && "¡Análisis listo!"}
                  {jobStatus === "FAILED" && "Ocurrió un error."}
                </div>
              )}

              {jobStatus !== "DONE" && (
                <p className="mt-3 text-center text-xs text-[#B3B3B3]">
                  El análisis puede tardar algunos segundos.
                </p>
              )}
            </div>
          </section>
        </form>
      </div>
    </main>
  );
}