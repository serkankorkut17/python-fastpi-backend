import os
import ssl
import uuid
import json
import asyncio
import time
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Request, APIRouter

from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay, MediaRecorder
from av import VideoFrame

from app.utils import logger


chat_router = APIRouter()

# Tüm aktif peer connection'ları; her bağlantı bir dict içerisinde saklanıyor.
# Örnek: pcs[pc_id] = {"pc": RTCPeerConnection, "username": "isim"}
pcs = {}

# Yayınlanan (publishing) track’ler; SFU mantığında, bir kullanıcının gönderdiği medya,
# diğer istemcilere relay edilmek üzere burada tutulur.
published_tracks = (
    []
)  # Her eleman: {"pc_id": ..., "track": ..., "username": ..., "kind": ...}

# MediaRelay nesnesi; bir track’i abone (subscribe) ederek birden fazla bağlantıya aktarabiliyoruz.
relay = MediaRelay()

# Chat geçmişi
chat_history = []
MAX_CHAT_HISTORY = 100  # Saklanacak maksimum mesaj sayısı

# WebSocket bağlantılarının takibi (chat için)
websocket_clients = {}

datachannels = {}

# Kayıtların saklanacağı dizin
RECORDINGS_DIR = "recordings"
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)


# ---------------------------
# /offer: WebRTC bağlantısı kurulumu için HTTP POST endpoint'i
# ---------------------------
@chat_router.post("/offer")
async def offer(request: Request):
    """
    İstemciden gelen SDP offer bilgisi alınır, yeni RTCPeerConnection oluşturulur.
    Ayrıca, mevcut yayınlanmış (published) track’ler yeni bağlantıya eklenir.
    İstemci isteği JSON şeklinde; örneğin:
    {
        "sdp": "...",
        "type": "offer",
        "username": "kullanici1"
    }
    """
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    username = params.get("username", "anonymous")
    client_id = params.get("client_id")

    # Yeni peer connection oluşturuluyor
    pc = RTCPeerConnection()
    pc_id = str(uuid.uuid4())
    pcs[pc_id] = {"pc": pc, "username": username, "client_id": client_id}
    logger.info(f"Yeni PC oluşturuldu: {pc_id} - {username}")

    # DataChannel event'ini yakalıyoruz.
    @pc.on("datachannel")
    def on_datachannel(channel):
        logger.info(f"DataChannel '{channel.label}' {username} tarafından açıldı.")
        datachannels[username] = channel

        @channel.on("message")
        def on_message(message):
            try:
                data = json.loads(message)
            except Exception as e:
                logger.error(f"DataChannel mesajı JSON olarak çözümlenemedi: {e}")
                return

            # Eğer gelen mesaj 'ping' ise, 'pong' ile cevap veriyoruz.
            if data.get("type") == "ping" and "time" in data:
                response = json.dumps({"type": "pong", "time": data["time"]})
                channel.send(response)
                # logger.info(f"Ping alındı ({data['time']}), pong gönderildi.")

            # Gelen mesajı diğer kullanıcılara yönlendir
            elif data.get("type") == "broadcast":
                sender_username = username  # Mevcut kanalın kullanıcısı

                forwarded_message = json.dumps(
                    {
                        "type": "forwarded_message",
                        "sender": sender_username,
                        "content": data["content"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Mesajı diğer tüm data kanallarına gönder
                for other_username, other_channel in datachannels.items():
                    if (
                        other_username != sender_username
                    ):  # Kendine geri göndermemek için
                        try:
                            other_channel.send(forwarded_message)
                            logger.info(
                                f"Mesaj {other_username} kullanıcısına yönlendirildi."
                            )
                        except Exception as e:
                            logger.error(
                                f"Mesaj yönlendirme hatası ({other_username}): {e}"
                            )

    @pc.on("track")
    def on_track(track: MediaStreamTrack):
        logger.info(f"{username} tarafından {track.kind} track alındı.")

        # Track'i published_tracks listesine ekle
        published_track = {
            "pc_id": pc_id,
            "track": track,
            "username": username,
            "kind": track.kind,
        }
        published_tracks.append(published_track)

        # Gelen track, diğer tüm aktif bağlantılara ekleniyor (kendisi hariç)
        for other_pc_id, other_info in pcs.items():
            if other_pc_id != pc_id or True:
                other_pc = other_info["pc"]

                try:
                    # Track'i relay üzerinden subscribe et
                    relayed_track = relay.subscribe(track)

                    # Diğer peer'ın transceiver'larını kontrol et
                    existing_transceiver = None
                    for transceiver in other_pc.getTransceivers():
                        if (
                            transceiver.sender.track is None
                            and transceiver.receiver.track is None
                        ):
                            existing_transceiver = transceiver
                            break

                    if existing_transceiver:
                        logger.info(f"Mevcut transceiver kullanılıyor: {other_pc_id}")
                        existing_transceiver.sender.replaceTrack(relayed_track)
                    else:
                        logger.info(f"Yeni track ekleniyor: {other_pc_id}")
                        other_pc.addTrack(relayed_track)

                    logger.info(
                        f"{username}'dan {other_info['username']}'a track eklendi"
                    )

                    # Renegotiation'ı başlat
                    # asyncio.create_task(renegotiate_connection(other_pc))
                except Exception as e:
                    logger.error(
                        f"Track eklenirken hata ({other_pc_id} -> {other_info['username']}): {str(e)}"
                    )
                    logger.exception(e)

        # Eğer audio track ise arka planda kayıt görevi başlatılıyor.
        # if track.kind == "audio":
        #     asyncio.create_task(record_audio_in_segments(track, username))
        # Video track'i için kayıt başlatmak istiyorsanız
        # elif track.kind == "video":
        #     asyncio.create_task(record_video_in_segments(track, username))

        @track.on("ended")
        async def on_ended():
            logger.info(f"{username} - {track.kind} track sonlandırıldı.")
            published_tracks.remove(published_track)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"{username} - PC {pc_id} connection state: {pc.connectionState}")
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            pcs.pop(pc_id, None)

    # İstemciden gelen offer uygulanıyor, cevap oluşturuluyor.
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Yeni bağlantıya, halihazırda yayınlanan diğer kullanıcıların track’leri ekleniyor.
    for pub in published_tracks:
        if pub["pc_id"] != pc_id:
            try:
                pc.addTrack(relay.subscribe(pub["track"]))
            except Exception as e:
                logger.error(f"Yeni PC'ye mevcut track eklenirken hata: {e}")

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "pc_id": pc_id,
    }


# ---------------------------
# WebSocket Chat Endpoint
# ---------------------------
@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket üzerinden chat mesajları alır ve:
      - Gelen mesajları chat_history listesine ekler (MAX_CHAT_HISTORY ile sınırlandırılır)
      - Tüm bağlı istemcilere yayınlar.
    """
    await websocket.accept()
    # active_websockets.add(websocket)
    client_id = str(uuid.uuid4())
    username = f"Kullanıcı-{client_id[:8]}"  # Varsayılan kullanıcı adı
    websocket_clients[client_id] = websocket

    logger.info(f"Yeni WebSocket bağlantısı: {client_id}")

    await websocket.send_json(
        {
            "type": "connection_success",
            "client_id": client_id,
            "username": username,
            "chat_history": chat_history[-50:],
        }
    )

    # Bağlanan istemciye mevcut chat geçmişini gönder
    # await websocket.send_json({"type": "history", "data": chat_history})

    # Diğer kullanıcılara yeni kullanıcının katıldığını bildir
    system_message = {
        "type": "chat_message",
        "sender": "Sistem",
        "content": f"{username} sohbete katıldı",
        "timestamp": datetime.now().isoformat(),
    }
    await broadcast_message(system_message, exclude_client=None)

    try:
        while True:
            data = await websocket.receive_json()
            # Gelen veri örneğin: {"username": "kullanici1", "message": "Merhaba!"}
            if data["type"] == "chat_message":
                chat_msg = {
                    "type": "chat_message",
                    "sender": username,
                    "sender_id": client_id,
                    "content": data["content"],
                    "timestamp": datetime.now().isoformat(),
                }

                # Mesajı geçmişe ekle
                chat_history.append(chat_msg)
                if len(chat_history) > MAX_CHAT_HISTORY:
                    chat_history.pop(0)  # En eski mesajı çıkar

                # Tüm kullanıcılara yayınla
                await broadcast_message(chat_msg, exclude_client=None)

            elif data["type"] == "username_change":
                old_username = username
                username = data["username"]
                system_message = {
                    "type": "chat_message",
                    "sender": "Sistem",
                    "content": f"{old_username} şimdi {username} olarak biliniyor",
                    "timestamp": datetime.now().isoformat(),
                }
                await broadcast_message(system_message, exclude_client=None)

            # Tüm bağlı WebSocket'lere mesajı gönder
            # for connection in list(active_websockets):
            #     try:
            #         await connection.send_json({"type": "chat", "data": chat_message})
            #     except Exception as e:
            #         logger.error(f"Mesaj gönderilirken hata: {e}")
    except WebSocketDisconnect:
        # active_websockets.remove(websocket)
        websocket_clients.pop(client_id, None)
        logger.info("WebSocket bağlantısı sonlandırıldı.")


# ---------------------------
# Uygulama Kapanırken: Tüm peer connection'ları kapat
# ---------------------------
@chat_router.on_event("shutdown")
async def on_shutdown():
    coros = [info["pc"].close() for info in pcs.values()]
    await asyncio.gather(*coros)
    pcs.clear()
    logger.info("Tüm PC bağlantıları kapatıldı.")


@chat_router.get("/pcs")
async def get_pcs():
    # Aktif peer connection'ları listele
    return [
        {"pc_id": pc_id, "username": info["username"]} for pc_id, info in pcs.items()
    ]


async def broadcast_message(message, exclude_client=None):
    # Mesajı tüm bağlı kullanıcılara dağıt
    chat_history.append(message)
    if len(chat_history) > MAX_CHAT_HISTORY:
        chat_history.pop(0)

    for client_id, connection in websocket_clients.items():
        if client_id != exclude_client:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Mesaj gönderilirken hata: {client_id}: {e}")


async def renegotiate_connection(pc: RTCPeerConnection):
    """Triggers renegotiation when new tracks are added and handles the answer."""
    try:
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Find the associated client information
        for pc_id, info in pcs.items():
            if info["pc"] == pc:
                username = info["username"]
                pc_client_id = info["client_id"]
                break
        else:
            logger.error("Could not find PC info for renegotiation")
            return

        logger.info(f"Renegotiation triggered for {username}")

        # Send the offer through WebSocket
        message = {
            "type": "renegotiation",
            "sdp": pc.localDescription.sdp,
            "pc_id": pc_id,
        }

        # Find the client's WebSocket connection
        client_ws = websocket_clients.get(pc_client_id)
        if not client_ws:
            logger.error(f"No WebSocket connection found for client {pc_client_id}")
            return

        # Send the offer and wait for answer
        try:
            await client_ws.send_json(message)

            # Wait for the answer (implement with a timeout)
            MAX_WAIT = 20  # seconds
            start_time = time.time()

            while time.time() - start_time < MAX_WAIT:
                try:
                    response = await client_ws.receive_json()
                    if response.get("type") == "renegotiation_answer":
                        answer = RTCSessionDescription(
                            sdp=response["sdp"], type="answer"
                        )
                        await pc.setRemoteDescription(answer)
                        logger.info(f"Renegotiation completed for {username}")
                        return
                except Exception as e:
                    logger.error(f"Error receiving renegotiation answer: {e}")
                    break

                await asyncio.sleep(0.1)

            logger.error(f"Timeout waiting for renegotiation answer from {username}")

        except Exception as e:
            logger.error(f"Error sending renegotiation message to {pc_client_id}: {e}")

    except Exception as e:
        logger.error(f"Error during renegotiation: {e}")


# ---------------------------
# Audio kaydını segmentler halinde yapan fonksiyon
# ---------------------------
async def record_audio_in_segments(track: MediaStreamTrack, username: str):
    """
    Gelen audio track'ini 1 dakikalık dosyalar halinde kaydeder.
    """
    segment_duration = 60  # saniye cinsinden kayıt süresi

    try:
        while True:
            # Dosya adını timestamp ve kullanıcı adıyla oluşturun
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(RECORDINGS_DIR, f"{username}_{timestamp}.wav")
            logger.info(f"Kayıt başladı: {file_name}")

            # MediaRecorder oluşturuluyor
            recorder = MediaRecorder(file_name)
            recorder.addTrack(track)
            await recorder.start()

            try:
                # segment_duration saniye boyunca kaydı devam ettir
                await asyncio.sleep(segment_duration)
            except asyncio.CancelledError:
                break

            # Kayıt tamamlanıyor
            await recorder.stop()
            logger.info(f"Kayıt tamamlandı: {file_name}")

            # Eğer track kapandıysa döngüden çıkıyoruz.
            if track.readyState == "ended":
                logger.info("Track sonlandırıldı, kayıt döngüsü bitiriliyor.")
                break

    except Exception as e:
        logger.error(f"Kayıt işlemi sırasında hata: {e}")


async def record_video_in_segments(track: MediaStreamTrack, username: str):
    """
    Gelen video track'ini 1 dakikalık dosyalar halinde kaydeder.
    """
    segment_duration = 60  # saniye cinsinden kayıt süresi

    try:
        while True:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # Video dosyası için mp4 veya webm uzantısı kullanılabilir.
            file_name = os.path.join(RECORDINGS_DIR, f"{username}_{timestamp}.mp4")
            logger.info(f"Video kaydı başladı: {file_name}")

            recorder = MediaRecorder(file_name)
            recorder.addTrack(track)
            await recorder.start()

            try:
                await asyncio.sleep(segment_duration)
            except asyncio.CancelledError:
                break

            await recorder.stop()
            logger.info(f"Video kaydı tamamlandı: {file_name}")

            if track.readyState == "ended":
                logger.info("Video track sonlandırıldı, kayıt döngüsü bitiriliyor.")
                break

    except Exception as e:
        logger.error(f"Video kayıt işlemi sırasında hata: {e}")
