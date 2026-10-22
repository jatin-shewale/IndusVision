import { type FormEvent, useEffect, useRef, useState } from "react";
import { HardHat, ShieldCheck } from "lucide-react";
import Layout from "../components/Layout";
import { Panel, StatCard } from "../components/UI";
import api from "../api/client";
import type { Detection } from "../types";

export default function WorkerSafety() {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [inferenceResults, setInferenceResults] = useState<Array<{ class_name: string; confidence: number }>>([]);
  const [lastInferenceAt, setLastInferenceAt] = useState<Date | null>(null);
  const [uploading, setUploading] = useState(false);
  const [cameraRunning, setCameraRunning] = useState(false);
  const [inferenceError, setInferenceError] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const captureTimerRef = useRef<number | null>(null);
  const processingFrameRef = useRef(false);

  function stopCamera() {
    if (captureTimerRef.current !== null) window.clearInterval(captureTimerRef.current);
    captureTimerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraRunning(false);
  }

  async function analyzeCameraFrame() {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || processingFrameRef.current) return;
    processingFrameRef.current = true;
    try {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.78));
      if (!blob) throw new Error("Could not capture a frame from the camera.");
      const form = new FormData();
      form.append("file", blob, "camera-frame.jpg");
      form.append("camera_id", "CAM_01");
      const result = await api.post("/api/detections/infer", form);
      setAnnotatedImage(`data:image/jpeg;base64,${result.data.annotated_image}`);
      setInferenceResults(result.data.detections);
      setLastInferenceAt(new Date());
      setInferenceError("");
    } catch (error: any) {
      setInferenceError(error.response?.data?.detail || error.message || "Live camera inference failed.");
    } finally {
      processingFrameRef.current = false;
    }
  }

  async function startCamera() {
    setInferenceError("");
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera access requires HTTPS or localhost in a supported browser.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraRunning(true);
      setAnnotatedImage(null);
      setInferenceResults([]);
      setLastInferenceAt(null);
      captureTimerRef.current = window.setInterval(() => void analyzeCameraFrame(), 1000);
    } catch (error: any) {
      setInferenceError(error.response?.data?.detail || error.message || "Could not start the camera.");
      stopCamera();
    }
  }

  async function runInference(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!imageFile) return;

    const form = new FormData();
    form.append("file", imageFile);
    form.append("camera_id", "UPLOAD");
    setUploading(true);
    setInferenceError("");
    try {
      const result = await api.post("/api/detections/infer", form);
      setAnnotatedImage(`data:image/jpeg;base64,${result.data.annotated_image}`);
      setInferenceResults(result.data.detections);
      setLastInferenceAt(new Date());
      const res = await api.get("/api/detections", { params: { limit: 50 } });
      setDetections(res.data);
    } catch (error: any) {
      setInferenceError(error.response?.data?.detail || "Could not run PPE inference.");
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get("/api/detections", { params: { limit: 50 } });
        setDetections(res.data);
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 8000);
    return () => {
      clearInterval(interval);
      if (captureTimerRef.current !== null) window.clearInterval(captureTimerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const violationCount = detections.filter((d) => d.is_violation).length;
  const complianceRate = detections.length
    ? Math.round(((detections.length - violationCount) / detections.length) * 100)
    : 100;
  const latestHasViolation = inferenceResults.some((item) =>
    ["NO-Hardhat", "NO-Mask", "NO-Safety Vest"].includes(item.class_name)
  );

  return (
    <Layout title="Worker Safety">
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <StatCard label="Frames Logged" value={detections.length} icon={HardHat} />
          <StatCard label="Violations" value={violationCount} icon={HardHat} accent={violationCount ? "danger" : "safe"} />
          <StatCard label="Compliance Rate" value={`${complianceRate}%`} icon={ShieldCheck} accent={complianceRate > 90 ? "safe" : "amber"} />
        </div>

        <Panel title="Live Worker Safety Camera">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="relative aspect-video bg-panel2 border border-border rounded flex items-center justify-center overflow-hidden">
              <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-contain" />
              {!cameraRunning && <p className="absolute text-textmuted text-sm text-center px-6">Start the camera to capture live frames for the trained Worker-Safety model.</p>}
            </div>
            <div className="space-y-3">
              <div className="relative aspect-video bg-panel2 border border-border rounded flex items-center justify-center overflow-hidden">
                {annotatedImage ? (
                  <img src={annotatedImage} alt="Latest annotated worker safety inference" className="h-full w-full object-contain" />
                ) : (
                  <p className="text-textmuted text-sm text-center px-6">The latest annotated model result will appear here.</p>
                )}
              </div>
              <div className="rounded border border-border bg-panel2 p-4 min-h-36">
                <div className="flex items-center justify-between gap-3">
                  <h4 className="text-sm font-semibold text-textprimary">Latest inference</h4>
                  <span className={`rounded px-2 py-1 text-xs font-mono ${
                    latestHasViolation ? "bg-danger/15 text-danger" : lastInferenceAt ? "bg-safe/15 text-safe" : "bg-textmuted/15 text-textmuted"
                  }`}>
                    {latestHasViolation ? "PPE VIOLATION" : lastInferenceAt ? "NO VIOLATION" : cameraRunning ? "ANALYZING" : "WAITING"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-textmuted">
                  {lastInferenceAt ? `Updated ${lastInferenceAt.toLocaleTimeString()}` : cameraRunning ? "Waiting for the first camera result…" : "Start the camera to see live detections here."}
                </p>
                <div className="mt-3 space-y-2">
                  {inferenceResults.length ? inferenceResults.map((item, index) => (
                    <div key={`${item.class_name}-${index}`} className="flex justify-between gap-4 border-t border-border/60 pt-2 text-sm">
                      <span className="text-textprimary">{item.class_name}</span>
                      <span className="font-mono text-textmuted">{Math.round(item.confidence * 100)}%</span>
                    </div>
                  )) : lastInferenceAt ? (
                    <p className="border-t border-border/60 pt-2 text-sm text-safe">No objects detected in the latest frame.</p>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            {cameraRunning ? (
              <button type="button" onClick={stopCamera} className="rounded bg-danger px-4 py-2 text-sm font-semibold text-white">Stop camera</button>
            ) : (
              <button type="button" onClick={startCamera} className="rounded bg-amber px-4 py-2 text-sm font-semibold text-black">Start live camera</button>
            )}
            <span className="text-xs text-textmuted">Live frames use Worker-Safety/best.pt at 50% confidence.</span>
          </div>
          <form onSubmit={runInference} className="mt-4 flex flex-wrap items-center gap-3">
            <span className="text-sm text-textmuted">Or analyze a saved image:</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(event) => setImageFile(event.target.files?.[0] ?? null)}
              className="text-sm text-textmuted file:mr-3 file:rounded file:border-0 file:bg-panel2 file:px-3 file:py-2 file:text-text"
            />
            <button
              type="submit"
              disabled={!imageFile || uploading}
              className="rounded bg-amber px-4 py-2 text-sm font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading ? "Analyzing…" : "Analyze image"}
            </button>
          </form>
          {inferenceError && <p className="mt-3 text-sm text-danger">{inferenceError}</p>}
        </Panel>

        <Panel title="Detection Log">
          {loading ? (
            <p className="text-textmuted text-sm">Loading...</p>
          ) : detections.length === 0 ? (
            <p className="text-textmuted text-sm">No detections logged yet. Upload an image above or run the camera inference tool.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-textmuted font-mono text-xs uppercase border-b border-border">
                    <th className="py-2 pr-4">Time</th>
                    <th className="py-2 pr-4">Camera</th>
                    <th className="py-2 pr-4">Zone</th>
                    <th className="py-2 pr-4">Classes</th>
                    <th className="py-2 pr-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {detections.map((d) => (
                    <tr key={d.id} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-mono text-xs text-textmuted">{new Date(d.timestamp).toLocaleString()}</td>
                      <td className="py-2 pr-4">{d.camera_id}</td>
                      <td className="py-2 pr-4">{d.machine_zone || "—"}</td>
                      <td className="py-2 pr-4">{d.detections.map((x) => x.class_name).join(", ")}</td>
                      <td className="py-2 pr-4">
                        {d.is_violation ? (
                          <span className="text-danger font-mono text-xs">VIOLATION</span>
                        ) : (
                          <span className="text-safe font-mono text-xs">OK</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </Layout>
  );
}
