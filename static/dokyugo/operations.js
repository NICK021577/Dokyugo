(() => {
  const monitor = document.querySelector('[data-desk-monitor]');
  if (monitor) {
    let previous;
    async function poll() {
      if (document.hidden) return;
      try {
        const response = await fetch(monitor.dataset.snapshot, {headers: {'Accept': 'application/json'}});
        if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) return;
        const data = await response.json();
        for (const key of ['booked','walkin','completed','messages']) document.querySelectorAll(`[data-metric="${key}"]`).forEach(el => el.textContent = data[key]);
        if (previous && JSON.stringify(previous) !== JSON.stringify(data)) document.querySelector('[data-queue-change]')?.removeAttribute('hidden');
        previous = data;
      } catch (_) { /* Keep the current queue visible during a connection interruption. */ }
    }
    poll(); setInterval(poll, 15000);
    document.querySelector('[data-refresh-desk]')?.addEventListener('click', () => location.reload());
  }
  const cameraButton = document.querySelector('[data-start-scanner]');
  if (cameraButton) {
    const panel = document.querySelector('[data-scanner-panel]');
    const video = panel.querySelector('video');
    const status = document.querySelector('[data-scanner-status]');
    let stream, scanning = false;
    const stop = () => { scanning = false; stream?.getTracks().forEach(track => track.stop()); panel.hidden = true; };
    document.querySelector('[data-stop-scanner]').addEventListener('click', stop);
    window.addEventListener('pagehide', stop);
    cameraButton.addEventListener('click', async () => {
      if (!('BarcodeDetector' in window) || !navigator.mediaDevices?.getUserMedia) {
        status.textContent = 'Camera scanning is unavailable in this browser. Use a USB QR scanner or paste the ticket link below.'; return;
      }
      try {
        const detector = new BarcodeDetector({formats:['qr_code']});
        stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false});
        video.srcObject = stream; panel.hidden = false; await video.play(); scanning = true;
        status.textContent = 'Hold the resident’s QR code in front of the camera.';
        const scan = async () => {
          if (!scanning) return;
          try {
            const codes = await detector.detect(video);
            if (codes.length) {
              document.getElementById('id_ticket').value = codes[0].rawValue;
              stop(); status.textContent = 'QR captured. Preview the ticket and confirm the resident’s identity before recording arrival.';
              document.querySelector('[data-preview-ticket]').click(); return;
            }
          } catch (_) {}
          setTimeout(scan, 300);
        }; scan();
      } catch (_) { stop(); status.textContent = 'Camera could not be opened. Use a USB QR scanner or paste the ticket link.'; }
    });
  }
  document.querySelectorAll('.message-thread').forEach(thread => { thread.scrollTop = thread.scrollHeight; });
})();
