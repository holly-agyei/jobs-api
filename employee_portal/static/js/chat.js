document.addEventListener("DOMContentLoaded", () => {
  const config = window.chatConfig;
  if (!config || !window.io) {
    return;
  }

  const form = document.getElementById("chat-form");
  const messagesContainer = document.getElementById("chat-messages");
  const messageField = form ? form.querySelector("textarea") : null;
  const socket = io("/chat", { transports: ["websocket", "polling"] });

  const scrollToBottom = () => {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  };

  socket.on("connect", () => {
    socket.emit("join", { room: config.room });
  });

  socket.on("receive_message", (payload) => {
    if (!messagesContainer) {
      return;
    }
    const bubble = document.createElement("div");
    const isSender = Number(payload.sender_id) === Number(config.senderId);
    bubble.className = `mb-2 ${isSender ? "text-end" : ""}`;

    const wrapper = document.createElement("div");
    wrapper.className = `d-inline-block px-3 py-2 rounded-3 ${
      isSender ? "bg-primary text-white" : "bg-light"
    }`;
    const meta = document.createElement("div");
    meta.className = "small fw-bold";
    const senderLabel = isSender ? "You" : payload.sender_name || "User";
    const timestamp = new Date(payload.timestamp).toLocaleString();
    meta.textContent = `${senderLabel} · ${timestamp}`;

    const content = document.createElement("div");
    content.textContent = payload.content;

    wrapper.appendChild(meta);
    wrapper.appendChild(content);
    bubble.appendChild(wrapper);
    messagesContainer.appendChild(bubble);
    scrollToBottom();
  });

  if (form && messageField) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = messageField.value.trim();
      if (!text) {
        return;
      }
      socket.emit("send_message", {
        room: config.room,
        sender_id: config.senderId,
        receiver_id: config.receiverId,
        content: text,
      });
      messageField.value = "";
    });
  }

  scrollToBottom();
});

