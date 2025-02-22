from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aiortc import (
    RTCPeerConnection,
    RTCConfiguration,
    RTCIceServer,
    RTCIceCandidate,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaBlackhole, MediaRelay, MediaPlayer, MediaRecorder
from datetime import datetime
import json
import asyncio
import os
import uuid
from app.utils import logger

ws_router = APIRouter()


# Bağlantıları ve peer connection'ları saklayacağımız veri yapısı
peers = {}
relay = MediaRelay()

# Mesaj geçmişini saklayacağımız yapı (basit bir liste, gerçek uygulamada veritabanı kullanılabilir)
chat_history = []
MAX_CHAT_HISTORY = 100  # Saklanacak maksimum mesaj sayısı

# Kayıtların kaydedileceği dizin
RECORDINGS_DIR = "recordings"
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(uuid.uuid4())
    username = f"Kullanıcı-{client_id[:8]}"  # Varsayılan kullanıcı adı
    logger.info(f"Yeni istemci bağlandı: {client_id}")

    try:
        # Yeni bağlantı ekle
        peers[client_id] = {
            "websocket": websocket,
            "pc": None,
            "audio_tracks": [],
            "username": username,
        }

        # Bağlantı başarılı mesajı ve mevcut sohbet geçmişini gönder
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_success",
                    "client_id": client_id,
                    "username": username,
                    "chat_history": chat_history[-50:],  # Son 50 mesajı gönder
                }
            )
        )

        # Diğer kullanıcılara yeni kullanıcının katıldığını bildir
        system_message = {
            "type": "chat_message",
            "sender": "Sistem",
            "content": f"{username} sohbete katıldı",
            "timestamp": datetime.now().isoformat(),
        }
        await broadcast_message(system_message, exclude_client=None)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "chat_message":
                # Metin mesajını işle ve yayınla
                chat_msg = {
                    "type": "chat_message",
                    "sender": peers[client_id]["username"],
                    "sender_id": client_id,
                    "content": message["content"],
                    "timestamp": datetime.now().isoformat(),
                }

                # Mesajı geçmişe ekle
                chat_history.append(chat_msg)
                if len(chat_history) > MAX_CHAT_HISTORY:
                    chat_history.pop(0)  # En eski mesajı çıkar

                # Tüm kullanıcılara yayınla
                await broadcast_message(chat_msg, exclude_client=None)

            elif message["type"] == "username_change":
                # Kullanıcı adı değişikliği
                old_username = peers[client_id]["username"]
                new_username = message["username"]
                peers[client_id]["username"] = new_username

                # Değişikliği diğer kullanıcılara bildir
                name_change_msg = {
                    "type": "chat_message",
                    "sender": "Sistem",
                    "content": f"{old_username} şimdi {new_username} olarak biliniyor",
                    "timestamp": datetime.now().isoformat(),
                }
                await broadcast_message(name_change_msg, exclude_client=None)

            elif message["type"] == "offer":
                # WebRTC offer geldiğinde yeni peer connection oluştur
                # Doğru yapılandırmayı oluşturmak için
                configuration = RTCConfiguration(
                    iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
                )

                pc = RTCPeerConnection(configuration)

                peers[client_id]["pc"] = pc

                @pc.on("track")
                async def on_track(track):
                    if track.kind == "audio":
                        logger.info(
                            f"Backend: {peers[client_id]['username']} kullanıcısından ses verisi alındı"
                        )

                        # Ses verisini relay'e ekle
                        relayed_track = relay.subscribe(track)
                        peers[client_id]["audio_tracks"].append(relayed_track)

                        # Backend üzerinden diğer tüm kullanıcılara ilet
                        for peer_id, peer_data in peers.items():
                            if peer_id != client_id and peer_data["pc"]:
                                logger.info(
                                    f"Backend: {peers[client_id]['username']} -> {peer_data['username']} ses verisi iletiliyor"
                                )
                                sender = peer_data["pc"].addTrack(relayed_track)
                            elif peer_id == client_id and peer_data["pc"]:
                                logger.info(
                                    f"Backend: {peers[client_id]['username']} -> {peer_data['username']} ses verisi iletilmedi"
                                )
                                sender = peer_data["pc"].addTrack(
                                    relayed_track
                                )  # ***************

                        # Kayıt işlemini başlatmak için asenkron bir görev oluşturuyoruz
                        asyncio.create_task(
                            record_audio_in_segments(
                                relayed_track, peers[client_id]["username"]
                            )
                        )

                # Offer'ı ayarla
                offer = RTCSessionDescription(sdp=message["sdp"], type=message["type"])
                await pc.setRemoteDescription(offer)

                # Answer oluştur
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)

                response = {
                    "type": pc.localDescription.type,
                    "sdp": pc.localDescription.sdp,
                }
                await websocket.send_text(json.dumps(response))

                # Answer'ı istemciye gönder
                await websocket.send_text(
                    json.dumps({"type": "answer", "sdp": pc.localDescription.sdp})
                )

            elif message["type"] == "ice_candidate":
                # ICE adayını ekle
                if peers[client_id]["pc"]:
                    # candidate = RTCIceCandidate(
                    #     component=message["candidate"].get("component"),
                    #     foundation=message["candidate"].get("foundation"),
                    #     ip=message["candidate"].get("ip"),
                    #     port=message["candidate"].get("port"),
                    #     priority=message["candidate"].get("priority"),
                    #     protocol=message["candidate"].get("protocol"),
                    #     type=message["candidate"].get("type"),
                    #     sdpMid=message["candidate"].get("sdpMid"),
                    #     sdpMLineIndex=message["candidate"].get("sdpMLineIndex"),
                    # )
                    # logger.info(f"ICE adayı: ip={message['candidate']['ip']}, port={message['candidate']['port']}")
                    # logger.info(f"ICE adayı: sdpMid={message['candidate']['sdpMid']}, sdpMLineIndex={message['candidate']['sdpMLineIndex']}")
                    # logger.info(f"ICE adayı: foundation={message['candidate']['foundation']}, priority={message['candidate']['priority']}")
                    # logger.info(f"ICE adayı: protocol={message['candidate']['protocol']}, type={message['candidate']['type']}")
                    # logger.info(f"ICE adayı: component={message['candidate']['component']}")
                    try:
                        # await peers[client_id]["pc"].addIceCandidate(candidate)
                        await peers[client_id]["pc"].addIceCandidate(message["candidate"])
                        logger.info(f"ICE adayı eklendi: {message['candidate']}")
                    except Exception as e:
                        logger.error(f"ICE adayı eklenirken hata: {e}")

    except WebSocketDisconnect:
        logger.info(f"{client_id} bağlantısı kesildi")

    except Exception as e:
        logger.error(f"Websocket işlemi sırasında hata: {e}")

    finally:
        # Bağlantı koptuğunda temizlik yap
        await handle_disconnect(client_id)


async def record_audio_in_segments(track, username):
    """
    Gelen audio track'ini 1 dakikalık dosyalar halinde kaydeder.
    """
    segment_duration = 60  # saniye cinsinden kayıt süresi

    try:
        while True:
            # Dosya adını timestamp ve kullanıcı adıyla oluşturun
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(RECORDINGS_DIR, f"{username}_{timestamp}.wav")
            print(f"Kayıt başladı: {file_name}")

            # MediaRecorder oluşturuluyor
            recorder = MediaRecorder(file_name)
            recorder.addTrack(track)
            await recorder.start()

            try:
                # segment_duration saniye boyunca kaydı devam ettir
                await asyncio.sleep(segment_duration)
            except asyncio.CancelledError:
                # Eğer görev iptal edilirse, kaydı sonlandır
                break

            # Kayıt tamamlanıyor
            await recorder.stop()
            print(f"Kayıt tamamlandı: {file_name}")

            # Eğer track kapandıysa döngüden çıkabilirsiniz:
            if track.readyState == "ended":
                print("Track sonlandırıldı, kayıt döngüsü bitiriliyor.")
                break
    except Exception as e:
        logger.error(f"Kayıt işlemi sırasında hata: {e}")


async def handle_disconnect(client_id):
    if client_id in peers:
        username = peers[client_id]["username"]
        logger.info(f"{username} sohbetten ayrıldı")

        # Kullanıcının PC bağlantısını kapat
        if peers[client_id]["pc"]:
            await peers[client_id]["pc"].close()

        # Bu kullanıcının ses izlerini diğer kullanıcılardan kaldır
        for track in peers[client_id]["audio_tracks"]:
            track.stop()  # Track'i durdur


        # Kullanıcıyı listeden çıkar
        del peers[client_id]

        # Diğer kullanıcılara ayrılma bilgisi gönder
        system_message = {
            "type": "chat_message",
            "sender": "Sistem",
            "content": f"{username} sohbetten ayrıldı",
            "timestamp": datetime.now().isoformat(),
        }
        await broadcast_message(system_message, exclude_client=None)
    else:
        logger.error(f"Handle disconnect için client_id bulunamadı: {client_id}")


async def broadcast_message(message, exclude_client=None):
    # Mesajı tüm bağlı kullanıcılara dağıt
    chat_history.append(message)
    if len(chat_history) > MAX_CHAT_HISTORY:
        chat_history.pop(0)

    for client_id, client_data in peers.items():
        if exclude_client is None or client_id != exclude_client:
            try:
                await client_data["websocket"].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Mesaj gönderme hatası {client_id}: {e}")
                # await handle_disconnect(client_id)
