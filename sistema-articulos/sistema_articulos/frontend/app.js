const API = 'http://127.0.0.1:8000';
let rolActual = 'investigador';
let usuarioActualId = 1;

// ── TOAST ────────────────────────────────────────────────────
function mostrarToast(mensaje, tipo = 'success') {
    const t = document.getElementById('toast');
    t.textContent = mensaje;
    t.className = `toast ${tipo} show`;
    setTimeout(() => t.className = 'toast', 3000);
}

// ── NAVEGACIÓN ───────────────────────────────────────────────
function irA(vistaId, btnEl) {
    document.querySelectorAll('.vista').forEach(v => v.style.display = 'none');
    document.getElementById(vistaId).style.display = 'block';
    document.querySelectorAll('.nav-btn, .tab').forEach(b => b.classList.remove('activo'));
    document.querySelectorAll(`[data-vista="${vistaId}"]`).forEach(b => b.classList.add('activo'));
}

// ── ROL ──────────────────────────────────────────────────────
function cambiarRol() {
    rolActual = document.getElementById('selector-rol').value;
    const textoRol = document.getElementById('texto-rol');
    const descRol = document.getElementById('desc-rol');
    if (rolActual === 'administrador') {
        textoRol.textContent = 'Administrador';
        textoRol.style.color = 'var(--purple)';
        descRol.textContent = 'Ves todas las publicaciones pendientes y puedes aprobar cualquiera sin límite de tiempo.';
    } else {
        textoRol.textContent = 'Investigador';
        textoRol.style.color = 'var(--green)';
        descRol.textContent = 'Puedes registrar artículos y aprobar los tuyos dentro de 72 horas.';
    }
    const bandejaVisible = document.getElementById('vista-aprobaciones');
    if (bandejaVisible && bandejaVisible.style.display !== 'none') cargarAprobaciones();
}

// ── TARJETA ARTÍCULO ─────────────────────────────────────────
function tarjetaArticulo(art, mostrarSimilitud = false) {
    const sim = (mostrarSimilitud && (art.similitud || art.relevancia))
        ? `<span class="badge badge-sim">${art.similitud || art.relevancia}</span>` : '';
    const doi = art.doi ? `<div class="card-doi">DOI · ${art.doi}</div>` : '';
    const revista = art.revista ? ` · ${art.revista}` : '';
    return `
    <div class="card">
        ${doi}
        <div class="card-titulo">${art.titulo}</div>
        <div class="card-meta">${art.autores || 'Sin autor'}</div>
        <div class="card-revista">${art.fecha || ''}${revista}</div>
        <div class="card-resumen">${(art.resumen || '').slice(0, 200)}...</div>
        <div class="card-footer">
            <a href="${art.enlace}" target="_blank" class="btn btn-secondary">Ver artículo →</a>
            ${sim}
        </div>
    </div>`;
}

// ── VISTA 1: ARTÍCULOS RECIENTES ─────────────────────────────
async function cargarArticulos() {
    const c = document.getElementById('lista-articulos');
    c.innerHTML = '<div class="estado"><span>⏳</span>Cargando...</div>';
    try {
        const res = await fetch(`${API}/articulos`);
        const data = await res.json();
        if (!data.articulos.length) {
            c.innerHTML = '<div class="estado"><span>📭</span>No hay artículos disponibles.</div>';
            return;
        }
        document.getElementById('total-articulos').textContent = data.total;
        document.getElementById('titulo-seccion').textContent = `Artículos recientes (${data.total})`;
        c.innerHTML = data.articulos.map(a => tarjetaArticulo(a)).join('');
    } catch {
        c.innerHTML = '<div class="estado"><span>⚠️</span>Error conectando con el servidor.<br><small>Verifica que el servidor esté corriendo en http://127.0.0.1:8000</small></div>';
    }
}

// ── BUSCADOR SEMÁNTICO ───────────────────────────────────────
async function buscar() {
    const q = document.getElementById('input-busqueda').value.trim();
    if (!q) return;
    irA('vista-articulos', null);
    document.querySelectorAll('[data-vista="vista-articulos"]').forEach(b => b.classList.add('activo'));
    const c = document.getElementById('lista-articulos');
    c.innerHTML = '<div class="estado generando"><span>🔍</span>Buscando con IA...</div>';
    try {
        const res = await fetch(`${API}/buscar?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        document.getElementById('titulo-seccion').textContent = `Resultados para "${q}" (${data.total})`;
        if (!data.resultados.length) {
            c.innerHTML = '<div class="estado"><span>🔎</span>Sin resultados para esa búsqueda.</div>';
            return;
        }
        c.innerHTML = data.resultados.map(a => tarjetaArticulo(a, true)).join('');
    } catch {
        c.innerHTML = '<div class="estado"><span>⚠️</span>Error en la búsqueda.</div>';
    }
}

document.getElementById('input-busqueda').addEventListener('keypress', e => {
    if (e.key === 'Enter') buscar();
});

// ── VISTA 2: RECOMENDACIONES ─────────────────────────────────
async function cargarRecomendaciones() {
    const c = document.getElementById('lista-recomendaciones');
    c.innerHTML = '<div class="estado generando"><span>🤖</span>Calculando recomendaciones...</div>';
    try {
        const res = await fetch(`${API}/recomendaciones/${usuarioActualId}`);
        const data = await res.json();
        if (!data.recomendaciones || !data.recomendaciones.length) {
            c.innerHTML = '<div class="estado"><span>📭</span>No hay recomendaciones disponibles aún.</div>';
            return;
        }
        c.innerHTML = data.recomendaciones.map(a => tarjetaArticulo(a)).join('');
    } catch {
        c.innerHTML = '<div class="estado"><span>⚠️</span>Error cargando recomendaciones.</div>';
    }
}

// ── VISTA 3: BANDEJA DE APROBACIÓN ───────────────────────────
async function cargarAprobaciones() {
    const c = document.getElementById('lista-aprobaciones');
    const titulo = document.getElementById('titulo-bandeja');
    c.innerHTML = '<div class="estado generando"><span>📬</span>Cargando bandeja...</div>';
    try {
        const res = await fetch(`${API}/publicaciones/pendientes`);
        const data = await res.json();
        titulo.textContent = rolActual === 'administrador'
            ? `Bandeja administrador — todas las pendientes (${data.total})`
            : `Bandeja investigador — publicaciones pendientes (${data.total})`;
        if (!data.publicaciones.length) {
            c.innerHTML = `<div class="estado"><span>✅</span>
                No hay publicaciones pendientes.<br>
                Ve a <strong>Mis artículos</strong> y genera publicaciones para un artículo.
            </div>`;
            return;
        }
        c.innerHTML = data.publicaciones.map(pub => {
            const vencida = pub.vencida;
            const puedeAprobar = rolActual === 'administrador' || !vencida;
            const botonesCompartir = botonesRedSocial(pub.id, pub.red_social);
            return `
            <div class="aprobacion-card" id="pub-${pub.id}">
                <span class="red-badge red-${pub.red_social}">${pub.red_social.toUpperCase()}</span>
                ${vencida ? `<div class="vencida-tag">⚠️ Plazo de 72h vencido — solo el administrador puede aprobar</div>` : ''}
                <div style="font-size:12px;color:var(--text3);margin-bottom:10px;">
                    ${pub.titulo.slice(0, 70)}...
                </div>
                <textarea class="aprobacion-texto" id="contenido-${pub.id}"
                    ${!puedeAprobar ? 'readonly' : ''}
                >${pub.contenido}</textarea>
                <div class="aprobacion-hint">
                    ${puedeAprobar ? 'Puedes editar el texto antes de aprobar.' : ''}
                </div>
                <div class="aprobacion-btns" id="btns-${pub.id}">
                    ${puedeAprobar ? `
                        <button class="btn btn-primary" onclick="aprobar(${pub.id})">✓ Aprobar</button>
                        <button class="btn btn-danger"  onclick="rechazar(${pub.id})">✗ Rechazar</button>
                    ` : `<span style="font-size:12px;color:var(--amber);">
                        Solo el administrador puede aprobar esta publicación
                    </span>`}
                    <button class="btn btn-copy" id="btn-copiar-${pub.id}"
                        onclick="copiarContenido(${pub.id})">📋 Copiar</button>
                    ${botonesCompartir}
                </div>
            </div>`;
        }).join('');
    } catch {
        c.innerHTML = '<div class="estado"><span>⚠️</span>Error cargando la bandeja.</div>';
    }
}

// ── BOTONES POR RED SOCIAL ───────────────────────────────────
function botonesRedSocial(pubId, red) {
    const botones = {
        whatsapp: `<button class="btn btn-wa"        onclick="compartirWhatsApp(${pubId})">📱 Enviar por WhatsApp</button>`,
        linkedin: `<button class="btn btn-secondary" onclick="abrirLinkedIn(${pubId})">💼 Abrir LinkedIn</button>`,
        twitter: `<button class="btn btn-secondary" onclick="abrirTwitter(${pubId})">🐦 Publicar en X</button>`,
        instagram: `<button class="btn btn-secondary" onclick="copiarParaInstagram(${pubId})">📸 Copiar para Instagram</button>`
    };
    return botones[red] || '';
}

// ── APROBAR / RECHAZAR ───────────────────────────────────────
async function aprobar(id) {
    try {
        await fetch(`${API}/publicaciones/aprobar/${id}`, { method: 'POST' });
        const card = document.getElementById(`pub-${id}`);
        card.style.borderLeftColor = 'var(--green)';
        card.style.opacity = '0.7';
        document.getElementById(`btns-${id}`).innerHTML =
            '<div style="color:var(--green);font-weight:600;font-size:13px;">✓ Aprobada — lista para publicar</div>';
        mostrarToast('✓ Publicación aprobada correctamente');
    } catch {
        mostrarToast('Error al aprobar la publicación', 'error');
    }
}

async function rechazar(id) {
    const card = document.getElementById(`pub-${id}`);
    card.style.borderLeftColor = 'var(--red)';
    card.style.opacity = '0.6';
    document.getElementById(`btns-${id}`).innerHTML =
        '<div style="color:var(--red);font-weight:600;font-size:13px;">✗ Rechazada</div>';
    mostrarToast('Publicación rechazada');
}

// ── COMPARTIR EN REDES ───────────────────────────────────────
function copiarContenido(pubId) {
    const contenido = document.getElementById(`contenido-${pubId}`).value;
    navigator.clipboard.writeText(contenido).then(() => {
        const btn = document.getElementById(`btn-copiar-${pubId}`);
        const original = btn.textContent;
        btn.textContent = '✓ Copiado';
        btn.style.background = 'var(--green)';
        btn.style.color = '#0d0f1a';
        setTimeout(() => {
            btn.textContent = original;
            btn.style.background = '';
            btn.style.color = '';
        }, 2000);
        mostrarToast('✓ Texto copiado al portapapeles');
    });
}

function compartirWhatsApp(pubId) {
    const contenido = document.getElementById(`contenido-${pubId}`).value;
    const url = `https://wa.me/?text=${encodeURIComponent(contenido)}`;
    window.open(url, '_blank');
    mostrarToast('📱 Abriendo WhatsApp...');
}

function abrirLinkedIn(pubId) {
    const contenido = document.getElementById(`contenido-${pubId}`).value;
    navigator.clipboard.writeText(contenido).then(() => {
        window.open('https://www.linkedin.com/feed/', '_blank');
        mostrarToast('💼 Texto copiado — pégalo en LinkedIn');
    });
}

function abrirTwitter(pubId) {
    const contenido = document.getElementById(`contenido-${pubId}`).value;
    const texto = contenido.slice(0, 270);
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(texto)}`;
    window.open(url, '_blank');
    mostrarToast('🐦 Abriendo Twitter/X...');
}

function copiarParaInstagram(pubId) {
    const contenido = document.getElementById(`contenido-${pubId}`).value;
    navigator.clipboard.writeText(contenido).then(() => {
        mostrarToast('📸 Texto copiado — pégalo en Instagram desde tu celular');
    });
}

// ── VISTA 4: MIS ARTÍCULOS ───────────────────────────────────
function cambiarTabRegistro(tipo) {
    document.getElementById('form-doi').style.display = tipo === 'doi' ? 'block' : 'none';
    document.getElementById('form-issn').style.display = tipo === 'issn' ? 'block' : 'none';
    document.getElementById('tab-doi').classList.toggle('activo', tipo === 'doi');
    document.getElementById('tab-issn').classList.toggle('activo', tipo === 'issn');
}

async function cargarMonitoreados() {
    const c = document.getElementById('lista-monitoreados');
    c.innerHTML = '<div class="estado generando"><span>📋</span>Cargando...</div>';
    try {
        const res = await fetch(`${API}/monitoreo/articulos`);
        const data = await res.json();
        document.getElementById('total-monitoreados').textContent = data.total;
        if (!data.articulos.length) {
            c.innerHTML = `<div class="estado"><span>➕</span>
                Aún no hay artículos registrados.<br>Agrega el primero con su DOI.
            </div>`;
            return;
        }
        c.innerHTML = data.articulos.map(art => `
            <div class="card" id="art-${art.id}">
                ${art.doi ? `<div class="card-doi">DOI · ${art.doi}</div>` : ''}
                <div class="card-titulo">${art.titulo}</div>
                <div class="card-meta">${art.autores || 'Sin autor'}</div>
                <div class="card-revista">${art.fecha || ''}${art.revista ? ' · ' + art.revista : ''}</div>
                <div class="card-resumen">${(art.resumen || '').slice(0, 180)}...</div>
                <div class="card-footer">
                    <a href="${art.enlace}" target="_blank" class="btn btn-secondary">Ver artículo →</a>
                    <button class="btn btn-purple" id="btn-gen-${art.id}"
                        onclick="generarPublicaciones(${art.id}, this)">
                        📢 Generar publicaciones
                    </button>
                    <button class="btn btn-danger"
                        onclick="eliminarArticulo('${art.uuid}', ${art.id})">
                        🗑 Eliminar
                    </button>
                </div>
                <div id="estado-${art.id}" style="margin-top:8px;font-size:12px;"></div>
            </div>`).join('');
    } catch {
        c.innerHTML = '<div class="estado"><span>⚠️</span>Error cargando artículos.</div>';
    }
}

async function registrarPorDoi() {
    const input = document.getElementById('input-doi');
    const mensaje = document.getElementById('mensaje-registro');
    const doi = input.value.trim();
    if (!doi) return;
    mensaje.style.color = 'var(--text3)';
    mensaje.textContent = '⏳ Consultando CrossRef...';
    try {
        const res = await fetch(
            `${API}/doi/registrar?doi=${encodeURIComponent(doi)}&registrado_por=${rolActual}`,
            { method: 'POST' }
        );
        const data = await res.json();
        if (data.exito) {
            mensaje.style.color = 'var(--green)';
            mensaje.innerHTML = `✓ ${data.mensaje}<br>
                <span style="color:var(--text3);">
                    <strong>${data.articulo.titulo.slice(0, 60)}...</strong><br>
                    ${data.articulo.revista || ''} · ${data.articulo.fecha || ''}
                </span>`;
            input.value = '';
            mostrarToast('✓ Artículo registrado correctamente');
            cargarMonitoreados();
        } else {
            mensaje.style.color = 'var(--red)';
            mensaje.textContent = '✗ ' + data.mensaje;
            mostrarToast(data.mensaje, 'error');
        }
    } catch {
        mensaje.style.color = 'var(--red)';
        mensaje.textContent = '✗ Error conectando con el servidor.';
        mostrarToast('Error conectando con el servidor', 'error');
    }
}

async function registrarPorIssn() {
    const input = document.getElementById('input-issn');
    const mensaje = document.getElementById('mensaje-registro');
    const issn = input.value.trim();
    if (!issn) return;
    mensaje.style.color = 'var(--text3)';
    mensaje.textContent = '⏳ Importando artículos de la revista...';
    try {
        const res = await fetch(
            `${API}/doi/registrar-issn?issn=${encodeURIComponent(issn)}&registrado_por=${rolActual}`,
            { method: 'POST' }
        );
        const data = await res.json();
        if (data.exito) {
            mensaje.style.color = 'var(--green)';
            mensaje.textContent = `✓ ${data.mensaje}`;
            input.value = '';
            mostrarToast(`✓ ${data.mensaje}`);
            cargarMonitoreados();
        } else {
            mensaje.style.color = 'var(--red)';
            mensaje.textContent = '✗ ' + data.mensaje;
            mostrarToast(data.mensaje, 'error');
        }
    } catch {
        mensaje.style.color = 'var(--red)';
        mensaje.textContent = '✗ Error conectando con el servidor.';
    }
}

async function generarPublicaciones(articuloId, btn) {
    const estado = document.getElementById(`estado-${articuloId}`);
    btn.disabled = true;
    btn.textContent = '⏳ Generando...';
    btn.style.opacity = '0.7';
    estado.className = 'generando';
    estado.textContent = 'La IA está generando las 4 publicaciones para redes sociales...';
    try {
        await fetch(`${API}/publicaciones/generar/${articuloId}`, { method: 'POST' });
        btn.textContent = '✓ Publicaciones generadas';
        btn.style.background = 'var(--green)';
        btn.style.color = '#0d0f1a';
        btn.style.opacity = '1';
        estado.className = '';
        estado.style.color = 'var(--green)';
        estado.innerHTML = `✓ LinkedIn, Twitter/X, Instagram y WhatsApp listos.<br>
            <span style="color:var(--text3);">
                Ve a la pestaña <strong>Bandeja autor</strong> para revisarlas y aprobarlas.
            </span>`;
        mostrarToast('✓ Publicaciones generadas — revísalas en Bandeja autor');
    } catch {
        btn.disabled = false;
        btn.textContent = '📢 Generar publicaciones';
        btn.style.opacity = '1';
        estado.className = '';
        estado.style.color = 'var(--red)';
        estado.textContent = '✗ Error generando publicaciones. Intenta de nuevo.';
        mostrarToast('Error generando publicaciones', 'error');
    }
}

// ── ELIMINAR ARTÍCULO ────────────────────────────────────────
async function eliminarArticulo(uuid, artId) {
    const confirmar = confirm('¿Quieres eliminar este artículo del monitoreo?');
    if (!confirmar) return;

    try {
        const res = await fetch(
            `${API}/monitoreo/eliminar/${uuid}`,
            { method: 'DELETE' }
        );
        const data = await res.json();

        if (res.ok) {
            const card = document.getElementById(`art-${artId}`);
            card.style.transition = 'opacity 0.3s';
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                cargarMetricas();
            }, 300);
            mostrarToast('✓ Artículo eliminado del monitoreo');
        } else {
            mostrarToast('Error al eliminar el artículo', 'error');
        }
    } catch {
        mostrarToast('Error conectando con el servidor', 'error');
    }
}

// ── MÉTRICAS ─────────────────────────────────────────────────
async function cargarMetricas() {
    try {
        const r1 = await fetch(`${API}/articulos`);
        const d1 = await r1.json();
        document.getElementById('total-articulos').textContent = d1.total;
    } catch { }
    try {
        const r2 = await fetch(`${API}/monitoreo/articulos`);
        const d2 = await r2.json();
        document.getElementById('total-monitoreados').textContent = d2.total;
    } catch { }
}

// ── INICIO ───────────────────────────────────────────────────
cargarArticulos();
cargarMetricas();
// ── DASHBOARD ─────────────────────────────────────────────
let graficaEvolucion = null;
let graficaRedes = null;

async function cargarDashboard() {
    try {
        const res = await fetch(`${API}/dashboard/metricas`);
        const data = await res.json();

        // Resumen
        document.getElementById('dash-articulos').textContent = data.resumen.total_articulos;
        document.getElementById('dash-vistas').textContent = data.resumen.total_vistas;
        document.getElementById('dash-descargas').textContent = data.resumen.total_descargas;
        document.getElementById('dash-eventos').textContent = data.resumen.total_eventos;

        // Gráfica evolución
        dibujarEvolucion(data.evolucion);

        // Gráfica por red
        dibujarRedes(data.por_red);

        // Ranking artículos
        dibujarRanking(data.articulos);

        // Tabla detalle
        dibujarTabla(data.articulos);

    } catch (e) {
        mostrarToast('Error cargando el dashboard', 'error');
    }
}

function dibujarEvolucion(evolucion) {
    const ctx = document.getElementById('grafica-evolucion').getContext('2d');
    if (graficaEvolucion) graficaEvolucion.destroy();

    const meses = evolucion.map(e => e.mes);
    const totales = evolucion.map(e => e.total);

    graficaEvolucion = new Chart(ctx, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [{
                label: 'Eventos',
                data: totales,
                borderColor: '#1a2a5e',
                backgroundColor: 'rgba(26,42,94,0.08)',
                borderWidth: 2,
                pointBackgroundColor: '#FFD100',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b90a8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b90a8' } }
            }
        }
    });
}

function dibujarRedes(porRed) {
    const ctx = document.getElementById('grafica-redes').getContext('2d');
    if (graficaRedes) graficaRedes.destroy();

    const colores = {
        web: '#7c6bff',
        linkedin: '#4d9ee8',
        twitter: '#aaa',
        instagram: '#f06292',
        whatsapp: '#4caf75'
    };

    const labels = porRed.map(r => r.red);
    const datos = porRed.map(r => r.total);
    const fondos = labels.map(l => colores[l] || '#555a75');

    graficaRedes = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: datos,
                backgroundColor: fondos,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#8b90a8', font: { size: 11 }, padding: 12 }
                }
            }
        }
    });
}

function dibujarRanking(articulos) {
    const c = document.getElementById('ranking-articulos');
    if (!articulos.length) {
        c.innerHTML = '<div style="color:var(--text3);font-size:12px;padding:12px 0;">Sin datos aún.</div>';
        return;
    }

    const maxEventos = Math.max(...articulos.map(a => a.total_eventos || 0), 1);

    c.innerHTML = articulos.slice(0, 5).map((art, i) => {
        const pct = Math.round(((art.total_eventos || 0) / maxEventos) * 100);
        const colores = ['#1a2a5e', '#FFD100', '#2a3e8e', '#e6bc00', '#8b90b8'];
        return `
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:12px;color:var(--text2);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    ${i + 1}. ${art.titulo.slice(0, 45)}...
                </span>
                <span style="font-size:12px;color:${colores[i]};margin-left:8px;white-space:nowrap;">
                    ${art.total_eventos || 0}
                </span>
            </div>
            <div style="height:4px;background:var(--bg3);border-radius:2px;">
                <div style="height:4px;width:${pct}%;background:${colores[i]};border-radius:2px;transition:width 0.5s;"></div>
            </div>
        </div>`;
    }).join('');
}

function dibujarTabla(articulos) {
    const c = document.getElementById('tabla-articulos');
    if (!articulos.length) {
        c.innerHTML = '<div style="color:var(--text3);font-size:12px;padding:12px 0;">Sin artículos monitoreados.</div>';
        return;
    }

    c.innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
            <tr style="border-bottom:1px solid var(--border);">
                <th style="text-align:left;padding:8px 4px;color:var(--text3);font-weight:500;">Artículo</th>
                <th style="text-align:center;padding:8px 4px;color:var(--text3);font-weight:500;">Vistas</th>
                <th style="text-align:center;padding:8px 4px;color:var(--text3);font-weight:500;">Descargas</th>
                <th style="text-align:center;padding:8px 4px;color:var(--text3);font-weight:500;">Total</th>
                <th style="text-align:left;padding:8px 4px;color:var(--text3);font-weight:500;">Revista</th>
            </tr>
        </thead>
        <tbody>
            ${articulos.map(art => `
            <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:10px 4px;color:var(--text2);max-width:300px;">
                    <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        ${art.titulo.slice(0, 50)}...
                    </div>
                    <div style="font-size:10px;color:var(--text3);margin-top:2px;">
                        ${art.autores ? art.autores.slice(0, 40) : ''}
                    </div>
                </td>
                <td style="text-align:center;padding:10px 4px;color:var(--purple);">
                    ${art.vistas || 0}
                </td>
                <td style="text-align:center;padding:10px 4px;color:var(--amber);">
                    ${art.descargas || 0}
                </td>
                <td style="text-align:center;padding:10px 4px;color:var(--green);font-weight:600;">
                    ${art.total_eventos || 0}
                </td>
                <td style="padding:10px 4px;color:var(--text3);font-size:11px;">
                    ${art.revista ? art.revista.slice(0, 30) : '—'}
                </td>
            </tr>`).join('')}
        </tbody>
    </table>`;
}