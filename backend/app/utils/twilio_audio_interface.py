import asyncio
from typing import Callable
import queue
import threading
import base64
from elevenlabs.conversational_ai.conversation import AudioInterface
import websockets

class TwilioAudioInterface(AudioInterface):
    def __init__(self, websocket):
        self.websocket = websocket
        self.output_queue = queue.Queue()
        self.should_stop = threading.Event()
        self.stream_sid = None
        self.input_callback = None
        self.output_thread = None
        self.host_availability = None
        self.media_packet_count = 0
        self.log_frequency = 20  # Log only every 20 packets

    def set_host_availability(self, availability):
        """Set the host's availability to be used in the conversation"""
        self.host_availability = availability
        print(f"Host availability set: {availability}")

    def start(self, input_callback: Callable[[bytes], None]):
        print("\n=== TWILIO AUDIO INTERFACE: STARTING ===\n")
        self.input_callback = input_callback
        self.output_thread = threading.Thread(target=self._output_thread)
        self.output_thread.start()
        print("\n=== TWILIO AUDIO INTERFACE: STARTED ===\n")

    def stop(self):
        print("\n=== TWILIO AUDIO INTERFACE: STOPPING ===\n")
        self.should_stop.set()
        if self.output_thread:
            self.output_thread.join(timeout=5.0)
        self.stream_sid = None
        print("\n=== TWILIO AUDIO INTERFACE: STOPPED ===\n")

    def output(self, audio: bytes):
        # Only log occasionally to reduce noise
        if not hasattr(self, 'output_count'):
            self.output_count = 0
        self.output_count += 1
        
        if self.output_count % 20 == 0:
            print(f"\n=== TWILIO AUDIO INTERFACE: OUTPUTTING AUDIO ===")
            print(f"Count: {self.output_count}")
            print(f"Size: {len(audio)} bytes")
            print(f"===========================================\n")
        
        self.output_queue.put(audio)

    def interrupt(self):
        try:
            while True:
                _ = self.output_queue.get(block=False)
        except queue.Empty:
            pass
        asyncio.run(self._send_clear_message_to_twilio())

    async def handle_twilio_message(self, data):
        try:
            if data["event"] == "start":
                self.stream_sid = data["start"]["streamSid"]
                print(f"Started stream with stream_sid: {self.stream_sid}")
            elif data["event"] == "media":
                self.media_packet_count += 1
                # Only log occasionally to reduce noise
                if self.media_packet_count % self.log_frequency == 0:
                    print(f"Received {self.media_packet_count} media packets so far (last: {len(data['media']['payload'])} bytes)")
                
                audio_data = base64.b64decode(data["media"]["payload"])
                if self.input_callback:
                    self.input_callback(audio_data)
            elif data["event"] == "stop":
                print(f"Stream stopped after {self.media_packet_count} media packets")
                self.stop()
        except Exception as e:
            print(f"Error in handle_twilio_message: {e}")

    def _output_thread(self):
        self.output_packet_count = 0
        while not self.should_stop.is_set():
            asyncio.run(self._send_audio_to_twilio())

    async def _send_audio_to_twilio(self):
        try:
            audio = self.output_queue.get(timeout=0.2)
            self.output_packet_count += 1
            
            # Only log occasionally
            if self.output_packet_count % self.log_frequency == 0:
                print(f"Sent {self.output_packet_count} audio packets to Twilio so far (last: {len(audio)} bytes)")
                
            audio_payload = base64.b64encode(audio).decode("utf-8")
            audio_delta = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": audio_payload},
            }
            await self.websocket.send_json(audio_delta)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error sending audio: {e}")

    async def _send_clear_message_to_twilio(self):
        try:
            clear_message = {"event": "clear", "streamSid": self.stream_sid}
            await self.websocket.send_json(clear_message)
        except Exception as e:
            print(f"Error sending clear message to Twilio: {e}") 