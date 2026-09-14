import asyncio
import os
import subprocess
import edge_tts
import imageio_ffmpeg

SCENES = [
    (
        "scene_1",
        "01 / PROBLEM · COMMUNITY ROSTER BURDEN",
        "In an extreme heat wave, the people who die are older, alone, and on somebody's list. "
        "Mutual-aid groups, congregations, block associations, and senior centers maintain rosters of vulnerable neighbors. "
        "But when an extreme heat dome settles over a city, a single volunteer coordinator cannot manually call dozens of residents, "
        "interpret ambiguous replies, and coordinate emergency transport before it is too late. "
        "Porchlight works the list automatically."
    ),
    (
        "scene_2",
        "02 / ARCHITECTURE · SERVERLESS & MULTI-AGENT RESILIENCE",
        "Here is how Porchlight works under the hood. "
        "National Weather Service alerts trigger an AWS EventBridge poller every fifteen minutes. "
        "When a heat warning activates, EventBridge invokes an AWS Bedrock AgentCore Runtime session. "
        "Using the Strands Agents framework, Porchlight spawns one dedicated resident agent per neighbor in parallel. "
        "Messages flow across Telegram, while critical medical decisions are intercepted by our human-in-the-loop Coordinator Gate. "
        "All state is immutably logged to Supabase under Row Level Security for the Next.js operator console."
    ),
    (
        "scene_3",
        "03 / LIVE DEMO · NWS HEAT ALERT & WAVE OUTREACH",
        "Let's see Porchlight in action. "
        "When the NWS issues an Extreme Heat Warning for Benton County, Porchlight detects the hazard "
        "and fires an automated outreach wave across all forty residents, prioritizing Tier 1 high-risk neighbors. "
        "Ruth Alvarez, an eighty-two-year-old resident living alone with limited mobility, "
        "instantly receives a personalized bilingual check-in on Telegram asking if she is safe, "
        "with clear reply options and mandatory opt-out protections."
    ),
    (
        "scene_4",
        "04 / LIVE DEMO · DETERMINISTIC WELLNESS SHORT-CIRCUIT",
        "Ruth replies with a quick '1'. "
        "Porchlight doesn't waste LLM tokens or introduce model latency for unambiguous answers. "
        "A deterministic short-circuit classifies simple wellness checks in just zero-point-eight-five seconds, "
        "instantly turning her status badge green on the operator board so the coordinator knows she is safe."
    ),
    (
        "scene_5",
        "05 / LIVE DEMO · MEDICAL DISTRESS & STRUCTURED TRIAGE",
        "Moments later, a critical reply arrives: 'AC broke, dizzy'. "
        "Strands triage analyzes the symptoms with Claude 3.5 Sonnet on Bedrock, "
        "extracts the exact quote for liability records, and classifies the situation as a medical emergency requiring cooling. "
        "But Porchlight never takes high-stakes actions autonomously, and our system never calls 911."
    ),
    (
        "scene_6",
        "06 / HUMAN GATE · STRANDS BEFORETOOLCALL INTERCEPT",
        "Instead, a Strands BeforeToolCall hook intercepts the execution, holds the automated action in a pending queue, "
        "and sends a single consolidated alert to the coordinator's phone. "
        "The coordinator sees the resident's name, triage reason, and numbered choices. "
        "Replying '1' authorizes dispatching a verified neighborhood volunteer."
    ),
    (
        "scene_7",
        "07 / DISPATCH · VOLUNTEER MATCHING & SCHEDULING",
        "Porchlight instantly matches the nearest open cooling center, identifies opted-in volunteer driver Marcus Webb, "
        "and texts him the transport request. "
        "Marcus replies 'Y' to accept. "
        "The dispatch updates to accepted in real time on the console, and a calendar event is scheduled—"
        "closing the critical loop in under two minutes."
    ),
    (
        "scene_8",
        "08 / SAFETY & EVALS · DEFENSE-IN-DEPTH & BENCHMARKS",
        "Safety is built into every layer. In synthetic mode, a strict phone allowlist guarantees zero texts escape the test perimeter. "
        "We enforce a strict never-911 policy, directing escalations to family and neighborhood emergency contacts. "
        "And our triage engine is battle-tested against thirty adversarial real-world replies—slang, typos, and Spanish idioms—"
        "achieving perfect one-hundred percent quote grounding and passing every benchmark."
    ),
    (
        "scene_9",
        "09 / CONCLUSION · RESILIENCE FOR EVERY NEIGHBOR",
        "Porchlight transforms an overwhelming spreadsheet into an intelligent, liability-grade safety net for community resilience. "
        "Because in a heat wave, no vulnerable neighbor should be left behind. "
        "Porchlight is completely open source under the MIT License. "
        "Thank you for watching."
    ),
]

def get_audio_duration(file_path):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-i", file_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            # HH:MM:SS.xx
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0

async def main():
    os.makedirs("build_media/audio", exist_ok=True)
    voice = "en-US-ChristopherNeural"
    total_dur = 0.0
    print(f"Using voice: {voice}")
    durations = {}
    for scene_id, label, text in SCENES:
        out_mp3 = f"build_media/audio/{scene_id}.mp3"
        comm = edge_tts.Communicate(text, voice, rate="+2%")
        await comm.save(out_mp3)
        dur = get_audio_duration(out_mp3)
        durations[scene_id] = dur
        total_dur += dur
        print(f"[{scene_id}] ({label}): {dur:.2f}s")

    print(f"\nTotal Audio Duration: {total_dur:.2f}s ({total_dur/60:.2f} minutes)")

if __name__ == "__main__":
    asyncio.run(main())
