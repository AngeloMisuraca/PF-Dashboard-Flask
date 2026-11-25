// Dibuja los gráficos interactivos a partir de los datos JSON que manda Python.
//
// Cada <div data-grafico> lleva dentro un <script type="application/json"> con el
// "spec" que generan logic/graficos.py y logic/tartas.py. Aquí solo se decide CÓMO se
// dibuja: los números y los textos (ya en formato español) vienen calculados de Python.
//
// Interacción:
//   · tooltips con el valor exacto al pasar el ratón (o tocar en el móvil)
//   · leyenda pulsable para ocultar o mostrar series
//   · tartas enlazadas con su tabla: al señalar una fila se resalta la porción
(function () {
    "use strict";

    var contenedores = document.querySelectorAll("[data-grafico]");
    if (!contenedores.length) { return; }

    if (!window.Chart) {
        contenedores.forEach(function (el) {
            var aviso = document.createElement("p");
            aviso.className = "lienzo__aviso";
            aviso.textContent = "No se ha podido cargar la librería de gráficos. Comprueba la conexión y recarga la página; los datos también están en la tabla.";
            el.appendChild(aviso);
        });
        return;
    }

    var TINTA = "#241A16", GRIS = "#74675E", REJILLA = "#ECE6E1", NOCHE = "#22080D", PAPEL = "#F6E7CF";
    var reducido = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (window.ChartDataLabels) { Chart.register(window.ChartDataLabels); }
    Chart.defaults.font.family = '"Hanken Grotesk", system-ui, sans-serif';
    Chart.defaults.font.size = 13;
    Chart.defaults.color = GRIS;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.animation = reducido ? false : { duration: 650, easing: "easeOutQuart" };
    Chart.defaults.plugins.datalabels = { display: false };
    Chart.defaults.plugins.legend.position = "bottom";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyle = "rectRounded";
    Chart.defaults.plugins.legend.labels.padding = 18;
    Chart.defaults.plugins.legend.labels.color = TINTA;
    Chart.defaults.plugins.legend.labels.font = { weight: 600 };
    Object.assign(Chart.defaults.plugins.tooltip, {
        backgroundColor: NOCHE, titleColor: PAPEL, bodyColor: "#fff", padding: 12, cornerRadius: 10,
        boxPadding: 5, titleFont: { weight: 700 }, bodyFont: { size: 13 }, usePointStyle: true
    });

    // ---------------------------------------------------------------- utilidades
    function alfa(color, a) {
        var hex = Math.round(a * 255).toString(16).padStart(2, "0");
        return Array.isArray(color) ? color.map(function (c) { return c + hex; }) : color + hex;
    }

    function oscuro(hex) {
        var h = hex.replace("#", "").slice(0, 6);
        var r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.62;
    }

    function colorDe(dataset, i) {
        var c = dataset.borderColor && dataset._claro ? dataset.borderColor : dataset.backgroundColor;
        return Array.isArray(c) ? c[i] : c;
    }

    function crear(etiqueta, clase, padre) {
        var e = document.createElement(etiqueta);
        if (clase) { e.className = clase; }
        if (padre) { padre.appendChild(e); }
        return e;
    }

    function describir(canvas, el) {
        var raiz = el.closest("[data-grafico]");
        canvas.setAttribute("role", "img");
        canvas.setAttribute("aria-label", raiz ? raiz.dataset.alt : "Gráfico");
        return canvas;
    }

    function lienzo(el, alto) {
        var marco = crear("div", "lienzo__marco", el);
        marco.style.height = alto + "px";
        return describir(crear("canvas", null, marco), el);
    }

    function nota(el, texto) {
        if (texto) { crear("p", "lienzo__nota", el).textContent = texto; }
    }

    var tooltipTextos = {
        callbacks: {
            label: function (ctx) {
                return " " + ctx.dataset.label + ": " + ctx.dataset._textos[ctx.dataIndex];
            }
        }
    };

    // ---------------------------------------------------------------- barras verticales
    function barras(el, s) {
        var muchas = s.series.length > 2 || s.pequenas;
        var datasets = s.series.map(function (se) {
            return {
                label: se.nombre, data: se.valores, _textos: se.textos, _dentro: se.dentro, _claro: !!se.claro,
                backgroundColor: se.claro ? alfa(se.color, 0.28) : se.color,
                hoverBackgroundColor: se.claro ? alfa(se.color, 0.45) : se.color,
                borderColor: se.color, borderWidth: se.claro ? 2 : 0,
                borderRadius: 6, borderSkipped: "start", maxBarThickness: 76,
                categoryPercentage: 0.72, barPercentage: 0.9
            };
        });
        new Chart(lienzo(el, s.alto), {
            type: "bar",
            data: { labels: s.etiquetas, datasets: datasets },
            options: {
                layout: { padding: { top: 26 } },
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: { grid: { display: false }, border: { display: false },
                         ticks: { color: TINTA, font: { weight: 600 } } },
                    y: { display: !!s.eje_y, beginAtZero: true, max: s.max, grace: s.max ? 0 : "14%",
                         border: { display: false }, grid: { color: REJILLA },
                         title: { display: !!s.eje, text: s.eje, color: GRIS },
                         ticks: { callback: function (v) { return v.toLocaleString("es-ES") + (s.unidad === "%" ? " %" : ""); } } }
                },
                plugins: {
                    legend: { display: s.leyenda !== false && s.series.length > 1 },
                    tooltip: tooltipTextos,
                    datalabels: {
                        display: true,
                        labels: {
                            valor: {
                                anchor: "end", align: "end", offset: 2, color: TINTA,
                                font: { weight: 700, size: muchas ? 11 : 13 },
                                formatter: function (v, ctx) { return v === null ? "" : ctx.dataset._textos[ctx.dataIndex]; }
                            },
                            dentro: {
                                display: function (ctx) { return !!(ctx.dataset._dentro && ctx.dataset._dentro[ctx.dataIndex]); },
                                anchor: "center", align: "center", color: "#fff", textAlign: "center",
                                font: { weight: 700, size: 12 },
                                formatter: function (v, ctx) { return ctx.dataset._dentro ? ctx.dataset._dentro[ctx.dataIndex] : ""; }
                            }
                        }
                    }
                }
            }
        });
    }

    // ---------------------------------------------------------------- barras verticales apiladas (con total)
    var totales = {
        id: "totales",
        afterDatasetsDraw: function (chart, _args, opciones) {
            if (!opciones.textos) { return; }
            var ctx = chart.ctx;
            ctx.save();
            ctx.font = "700 13px " + Chart.defaults.font.family;
            ctx.fillStyle = TINTA;
            ctx.textAlign = "center";
            opciones.textos.forEach(function (texto, i) {
                var arriba = null, x = null;
                chart.data.datasets.forEach(function (_d, di) {
                    if (!chart.isDatasetVisible(di)) { return; }
                    var barra = chart.getDatasetMeta(di).data[i];
                    if (barra && (arriba === null || barra.y < arriba)) { arriba = barra.y; x = barra.x; }
                });
                if (arriba !== null) { ctx.fillText(texto, x, arriba - 8); }
            });
            ctx.restore();
        }
    };

    function apiladas(el, s) {
        new Chart(lienzo(el, s.alto), {
            type: "bar",
            plugins: [totales],
            data: {
                labels: s.etiquetas,
                datasets: s.series.map(function (se) {
                    return { label: se.nombre, data: se.valores, _textos: se.textos, backgroundColor: se.color,
                             borderRadius: 4, maxBarThickness: 110 };
                })
            },
            options: {
                layout: { padding: { top: 28 } },
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: { stacked: true, grid: { display: false }, border: { display: false },
                         ticks: { color: TINTA, font: { weight: 600 } } },
                    y: { stacked: true, display: false, grace: "8%" }
                },
                plugins: {
                    totales: { textos: s.totales },
                    tooltip: tooltipTextos,
                    datalabels: {
                        display: function (ctx) {
                            var total = 0;
                            ctx.chart.data.datasets.forEach(function (d) { total += d.data[ctx.dataIndex] || 0; });
                            return ctx.dataset.data[ctx.dataIndex] / total > 0.08;
                        },
                        color: function (ctx) { return oscuro(colorDe(ctx.dataset, ctx.dataIndex)) ? "#fff" : TINTA; },
                        font: { weight: 700 },
                        formatter: function (v, ctx) { return ctx.dataset._textos[ctx.dataIndex]; }
                    }
                }
            }
        });
    }

    // ---------------------------------------------------------------- barras horizontales (ranking)
    function barrasH(el, s) {
        var se = s.series[0];
        var largos = se.textos.some(function (t) { return t.length > 12; });
        var fuerte = s.primero_fuerte !== false;      // la primera fila (España) en negrita
        new Chart(lienzo(el, s.alto), {
            type: "bar",
            data: {
                labels: s.etiquetas,
                datasets: [{ label: se.nombre, data: se.valores, _textos: se.textos, backgroundColor: se.color,
                             borderRadius: 5, borderSkipped: "start", barPercentage: 0.82, categoryPercentage: 0.9 }]
            },
            options: {
                indexAxis: "y",
                layout: { padding: { right: 8 } },
                scales: {
                    // divergente: barras a los dos lados del cero (cambios que suben y que bajan)
                    x: s.divergente
                        ? { grace: "22%", grid: { color: function (c) { return c.tick.value === 0 ? GRIS : "transparent"; } },
                            border: { display: false }, ticks: { display: false } }
                        : { display: false, beginAtZero: true, grace: largos ? "75%" : "16%" },
                    y: { grid: { display: false }, border: { display: false },
                         ticks: { color: TINTA, autoSkip: false,
                                  font: function (ctx) { return { size: 12.5, weight: s.divergente && ctx.index === 0 && fuerte ? 800 : 500 }; } } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: tooltipTextos,
                    datalabels: {
                        display: true, anchor: "end", align: "end", offset: 4, color: TINTA,
                        font: function (ctx) {
                            var negrita = !fuerte ? true : (s.divergente ? ctx.dataIndex === 0 : ctx.dataIndex < 3);
                            return { weight: negrita ? 700 : 500, size: fuerte ? 12 : 14 };
                        },
                        formatter: function (v, ctx) { return ctx.dataset._textos[ctx.dataIndex]; }
                    }
                }
            }
        });
        nota(el, s.nota);
    }

    // ---------------------------------------------------------------- líneas (evolución e índice 100)
    // Cada línea lleva su nombre y su último valor al final: no hace falta ir a la leyenda.
    // Etiquetas al final de cada línea; si dos quedan muy juntas, se separan en vertical
    var finales = {
        id: "finales",
        afterDatasetsDraw: function (chart, _args, o) {
            if (!o.activo) { return; }
            var ctx = chart.ctx, area = chart.chartArea, sep = 18, etiquetas = [];
            chart.data.datasets.forEach(function (d, i) {
                if (!chart.isDatasetVisible(i)) { return; }
                var puntos = chart.getDatasetMeta(i).data;
                for (var k = puntos.length - 1; k >= 0; k--) {
                    if (d.data[k] !== null && d.data[k] !== undefined) {
                        etiquetas.push({ x: puntos[k].x, y: puntos[k].y, texto: d._final, color: d.borderColor });
                        break;
                    }
                }
            });
            etiquetas.sort(function (a, b) { return a.y - b.y; });
            for (var j = 1; j < etiquetas.length; j++) {
                if (etiquetas[j].y - etiquetas[j - 1].y < sep) { etiquetas[j].y = etiquetas[j - 1].y + sep; }
            }
            var exceso = etiquetas.length ? etiquetas[etiquetas.length - 1].y - (area.bottom + 6) : 0;
            if (exceso > 0) { etiquetas.forEach(function (e) { e.y -= exceso; }); }
            ctx.save();
            ctx.font = "800 13px " + Chart.defaults.font.family;
            ctx.textBaseline = "middle";
            etiquetas.forEach(function (e) {
                ctx.fillStyle = e.color;
                ctx.fillText(e.texto, e.x + 12, e.y);
            });
            ctx.restore();
        }
    };

    // s.puntos: el valor encima de cada punto (paneles de un solo sector, sin etiqueta al final)
    // s.cero === false: el eje no empieza en 0 (cada panel usa la escala de sus propios valores)
    function lineas(el, s) {
        var estrecho = el.clientWidth < 560;
        var conFinales = !s.puntos && !estrecho;
        var largo = s.series.reduce(function (m, se) { return Math.max(m, (se.final || "").length); }, 0);
        new Chart(lienzo(el, s.alto), {
            type: "line",
            plugins: [finales],
            data: {
                labels: s.etiquetas,
                datasets: s.series.map(function (se) {
                    return { label: se.nombre, data: se.valores, _textos: se.textos, _final: se.final,
                             borderColor: se.color, backgroundColor: se.color, borderWidth: 3.5, tension: 0,
                             pointRadius: 5, pointHoverRadius: 8, pointBackgroundColor: se.color,
                             pointBorderColor: "#fff", pointBorderWidth: 2, spanGaps: true };
                })
            },
            options: {
                layout: { padding: { top: s.puntos ? 26 : 16, right: conFinales ? 24 + largo * 8 : 16, left: s.puntos ? 10 : 0 } },
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: { grid: { display: false }, border: { display: false }, offset: s.etiquetas.length === 1 || !!s.puntos,
                         ticks: { color: TINTA, font: { weight: 700, size: 13 } } },
                    y: { beginAtZero: s.cero !== false && (s.base === null || s.base === undefined), grace: "18%",
                         border: { display: false },
                         title: { display: !!s.eje, text: s.eje, color: GRIS },
                         grid: { color: function (c) { return s.base && c.tick.value === s.base ? GRIS : REJILLA; },
                                 lineWidth: function (c) { return s.base && c.tick.value === s.base ? 2 : 1; } },
                         ticks: { callback: function (v) { return v.toLocaleString("es-ES") + (s.unidad === "%" ? " %" : ""); } } }
                },
                plugins: {
                    legend: { display: estrecho && !s.puntos },
                    tooltip: tooltipTextos,
                    finales: { activo: conFinales },         // "Cine 66,9 M" al final de cada línea
                    datalabels: {
                        display: !!s.puntos, anchor: "end", align: "top", offset: 6, color: TINTA,
                        font: { weight: 700, size: 12.5 },
                        formatter: function (v, ctx) { return v === null ? "" : ctx.dataset._textos[ctx.dataIndex]; }
                    }
                }
            }
        });
        nota(el, s.nota);
    }

    // ---------------------------------------------------------------- barras horizontales al 100 %
    function apiladasH(el, s) {
        new Chart(lienzo(el, s.alto), {
            type: "bar",
            data: {
                labels: s.etiquetas,
                datasets: s.series.map(function (se) {
                    return { label: se.nombre, data: se.valores, _textos: se.textos, backgroundColor: se.color,
                             borderColor: "#fff", borderWidth: { left: 0, right: 2, top: 0, bottom: 0 },
                             barPercentage: 0.78, categoryPercentage: 0.92 };
                })
            },
            options: {
                indexAxis: "y",
                interaction: { mode: "index", intersect: false, axis: "y" },
                scales: {
                    x: { stacked: true, display: false, max: 100 },
                    y: { stacked: true, grid: { display: false }, border: { display: false },
                         ticks: {
                             color: TINTA, autoSkip: false,
                             font: function (ctx) { return { weight: s.etiquetas[ctx.index] === "España" ? 800 : 500, size: 12.5 }; }
                         } }
                },
                plugins: {
                    tooltip: tooltipTextos,
                    datalabels: {
                        display: function (ctx) { return ctx.dataset.data[ctx.dataIndex] >= 6.5; },
                        color: function (ctx) { return oscuro(colorDe(ctx.dataset, ctx.dataIndex)) ? "#fff" : TINTA; },
                        font: { weight: 700, size: 12 },
                        formatter: function (v, ctx) { return ctx.dataset._textos[ctx.dataIndex]; }
                    }
                }
            }
        });
    }

    // ---------------------------------------------------------------- burbujas
    var medias = {
        id: "medias",
        beforeDatasetsDraw: function (chart, _args, o) {
            var ctx = chart.ctx, area = chart.chartArea, x = chart.scales.x, y = chart.scales.y;
            ctx.save();
            ctx.strokeStyle = GRIS;
            ctx.setLineDash([5, 5]);
            ctx.lineWidth = 1;
            ctx.fillStyle = GRIS;
            ctx.font = "italic 12px " + Chart.defaults.font.family;
            if (o.x !== null && o.x !== undefined) {
                var px = x.getPixelForValue(o.x);
                ctx.beginPath(); ctx.moveTo(px, area.top); ctx.lineTo(px, area.bottom); ctx.stroke();
                ctx.fillText("media de España", px + 6, area.top + 12);
            }
            if (o.y !== null && o.y !== undefined) {
                var py = y.getPixelForValue(o.y);
                ctx.beginPath(); ctx.moveTo(area.left, py); ctx.lineTo(area.right, py); ctx.stroke();
            }
            ctx.restore();
        }
    };

    function burbujas(el, s) {
        var escala = el.clientWidth < 600 ? 0.6 : 1;
        new Chart(lienzo(el, s.alto), {
            type: "bubble",
            plugins: [medias],
            data: {
                datasets: [{
                    label: "Comunidades",
                    data: s.puntos.map(function (p) { return { x: p.x, y: p.y, r: p.r * escala, _p: p }; }),
                    backgroundColor: alfa(s.color, 0.42), borderColor: s.color, borderWidth: 1.5,
                    hoverBackgroundColor: alfa(s.color, 0.85), hoverBorderWidth: 2
                }]
            },
            options: {
                layout: { padding: 10 },
                scales: {
                    x: { grace: "8%", title: { display: true, text: s.eje_x, color: GRIS }, grid: { color: REJILLA },
                         border: { display: false },
                         ticks: { callback: function (v) { return v.toLocaleString("es-ES"); } } },
                    y: { grace: "10%", title: { display: true, text: s.eje_y, color: GRIS }, grid: { color: REJILLA },
                         border: { display: false },
                         ticks: { callback: function (v) { return v.toLocaleString("es-ES"); } } }
                },
                plugins: {
                    legend: { display: false },
                    medias: { x: s.media_x, y: s.media_y },
                    tooltip: {
                        callbacks: {
                            title: function (items) { return items[0].raw._p.nombre; },
                            label: function () { return ""; },
                            afterBody: function (items) { return items[0].raw._p.detalle; }
                        }
                    },
                    datalabels: {
                        display: "auto", clamp: true, anchor: "end", align: "end", offset: 0,
                        color: TINTA, font: { size: 11.5, weight: 600 },
                        formatter: function (v) { return v._p.nombre; }
                    }
                }
            }
        });
        nota(el, s.nota);
    }

    // ---------------------------------------------------------------- tartas enlazadas con su tabla
    function donut(contenedor, pcts, textos, colores, centro) {
        var caja = crear("div", "donut", contenedor);
        var canvas = describir(crear("canvas", null, caja), contenedor);
        var c = crear("div", "donut__centro", caja);
        crear("strong", null, c).textContent = centro[0];
        crear("span", null, c).textContent = centro[1];
        return new Chart(canvas, {
            type: "doughnut",
            data: { labels: [], datasets: [{ data: pcts, _textos: textos, backgroundColor: colores,
                                             borderColor: "#fff", borderWidth: 3, hoverOffset: 12 }] },
            options: {
                cutout: "56%", layout: { padding: 14 },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                    datalabels: {
                        display: function (ctx) { return ctx.dataset.data[ctx.dataIndex] >= 8; },
                        color: function (ctx) { return oscuro(colores[ctx.dataIndex]) ? "#fff" : TINTA; },
                        font: { weight: 700, size: 12 },
                        formatter: function (v, ctx) { return textos[ctx.dataIndex]; }
                    }
                }
            }
        });
    }

    // Une las tartas y las filas: señalar una cosa resalta la otra.
    function enlazar(graficos, filas) {
        function marcar(i) {
            filas.forEach(function (f, k) { f.classList.toggle("activa", k === i); });
            graficos.forEach(function (g) {
                g.setActiveElements(i === null ? [] : [{ datasetIndex: 0, index: i }]);
                g.update();
            });
        }
        filas.forEach(function (f, i) {
            f.tabIndex = 0;
            f.addEventListener("mouseenter", function () { marcar(i); });
            f.addEventListener("focus", function () { marcar(i); });
            f.addEventListener("mouseleave", function () { marcar(null); });
            f.addEventListener("blur", function () { marcar(null); });
        });
        graficos.forEach(function (g) {
            g.options.onHover = function (_e, activos) {
                var i = activos.length ? activos[0].index : null;
                filas.forEach(function (f, k) { f.classList.toggle("activa", k === i); });
                graficos.forEach(function (otro) {
                    if (otro !== g) { otro.setActiveElements(i === null ? [] : [{ datasetIndex: 0, index: i }]); otro.update(); }
                });
            };
        });
    }

    function fila(tbody, color, nombre, celdas) {
        var tr = crear("tr", null, tbody);
        var th = crear("th", null, tr);
        th.setAttribute("scope", "row");
        var muestra = crear("i", "muestra", th);
        muestra.style.background = color;
        th.appendChild(document.createTextNode(nombre));
        celdas.forEach(function (t, k) {
            var td = crear("td", k === 0 ? "fuerte" : "", tr);
            td.textContent = t;
        });
        return tr;
    }

    // Tartas del comparador: una por año y una tabla que las une (señalar una fila resalta su porción)
    function tartasAnios(el, s) {
        var tartas = crear("div", "donuts donuts--anios", el);
        var graficos = s.tartas.map(function (t) {
            var bloque = crear("div", "donuts__una", tartas);
            crear("h4", null, bloque).textContent = t.titulo;
            return donut(bloque, t.pcts, t.textos, s.colores, t.centro);
        });
        var tabla = crear("table", "donut-tabla", crear("div", "donut-tabla__wrap", el));
        var cab = crear("tr", null, crear("thead", null, tabla));
        crear("th", null, cab).textContent = "";
        s.anios.forEach(function (a) { crear("th", null, cab).textContent = a; });
        if (s.cambio) { crear("th", null, cab).textContent = s.cabecera_cambio; }
        var tbody = crear("tbody", null, tabla);
        var filas = s.nombres.map(function (n, i) {
            var celdas = s.tartas.map(function (t) { return t.textos[i]; });
            var tr = fila(tbody, s.colores[i], n, celdas);
            // en negrita, el último año (el más reciente), no el primero
            tr.cells[1].classList.remove("fuerte");
            tr.cells[s.tartas.length].classList.add("fuerte");
            if (s.cambio) {
                // el cambio, como en el resto de la web: verde si crece, rojo si se reduce
                var td = crear("td", "num", tr);
                crear("span", "cambio " + (s.tendencias ? s.tendencias[i] : ""), td).textContent = s.cambio[i];
            }
            return tr;
        });
        enlazar(graficos, filas);
    }

    // ---------------------------------------------------------------- varios paneles
    function paneles(el, s) {
        var rejilla = crear("div", "paneles", el);
        s.paneles.forEach(function (p) {
            var celda = crear("div", "paneles__uno", rejilla);
            crear("h4", null, celda).textContent = p.titulo;
            dibujar(celda, p);
        });
    }

    var tipos = {
        barras: barras, apiladas: apiladas, barras_h: barrasH, apiladas_h: apiladasH, burbujas: burbujas,
        paneles: paneles, lineas: lineas, tartas_anios: tartasAnios
    };

    function dibujar(el, s) {
        (tipos[s.tipo] || function () {})(el, s);
    }

    // Dibuja los gráficos que haya dentro de 'raiz'. app.js lo vuelve a llamar cuando
    // sustituye una sección al cambiar un filtro (sin recargar la página).
    function pintar(el) {
        var fuente = el.querySelector('script[type="application/json"]');
        if (!fuente || el.dataset.dibujado || !el.isConnected) { return; }
        el.dataset.dibujado = "1";
        try {
            dibujar(el, JSON.parse(fuente.textContent));
        } catch (error) {
            crear("p", "lienzo__aviso", el).textContent = "Este gráfico no se ha podido dibujar. Los datos están en la tabla de la página.";
            if (window.console) { console.error(error); }
        }
    }

    // Cada gráfico se dibuja cuando está a punto de verse, no todos a la vez: al cargar o al
    // cambiar un filtro, el navegador solo trabaja con los que tienes en pantalla.
    // Gráficos pendientes de dibujar: se pintan cuando están a punto de verse (a 600 px o menos).
    // Se comprueba al cargar, al desplazarse y al cambiar el tamaño de la ventana. (No se usa
    // IntersectionObserver: el hueco de un gráfico sin dibujar mide 0 px de alto y algunos
    // navegadores no avisan nunca de que es visible, así que el gráfico se quedaba en blanco.)
    var pendientes = [];
    var MARGEN = 600;

    function cerca(el) {
        var r = el.getBoundingClientRect(), alto = window.innerHeight || 800;
        return r.top < alto + MARGEN && r.bottom > -MARGEN;
    }

    function revisar() {
        pendientes = pendientes.filter(function (el) {
            if (el.dataset.dibujado || !el.isConnected) { return false; }
            if (cerca(el)) { pintar(el); return false; }
            return true;
        });
    }

    var esperando = false;
    function alMoverse() {
        if (esperando || !pendientes.length) { return; }
        esperando = true;
        // un temporizador y no requestAnimationFrame: este se pausa en pestañas o marcos ocultos
        // y entonces la comprobación se quedaba bloqueada para siempre
        setTimeout(function () { esperando = false; revisar(); }, 50);
    }
    window.addEventListener("scroll", alMoverse, { passive: true });
    window.addEventListener("resize", alMoverse);
    // Red de seguridad: mientras quede algún gráfico pendiente, se revisa cada 300 ms (por si el
    // navegador agrupa o no envía los eventos de scroll, p. ej. al saltar con un enlace). Se para sola.
    var ronda = null;
    function vigilarPendientes() {
        if (ronda || !pendientes.length) { return; }
        ronda = setInterval(function () {
            revisar();
            if (!pendientes.length) { clearInterval(ronda); ronda = null; }
        }, 300);
    }

    // inmediato = tras cambiar un filtro: los gráficos a la vista se dibujan ya y sin animación de
    // entrada, para que el cambio se vea al instante. "todos": la sección cambiada se dibuja entera.
    function dibujarEn(raiz, inmediato) {
        raiz.querySelectorAll("[data-grafico]").forEach(function (el) {
            if (el.dataset.dibujado) { return; }
            if (inmediato === "todos" || (inmediato && cerca(el))) {
                var antes = Chart.defaults.animation;
                Chart.defaults.animation = false;
                try { pintar(el); } finally { Chart.defaults.animation = antes; }
            } else if (cerca(el)) {
                pintar(el);
            } else if (pendientes.indexOf(el) < 0) {
                pendientes.push(el);
            }
        });
        vigilarPendientes();
    }

    // Antes de quitar una sección, libera sus gráficos (Chart.js guarda cada uno en memoria)
    function borrarEn(raiz) {
        pendientes = pendientes.filter(function (el) { return !raiz.contains(el); });
        raiz.querySelectorAll("canvas").forEach(function (c) {
            var g = Chart.getChart(c);
            if (g) { g.destroy(); }
        });
    }

    window.Graficos = { dibujar: dibujarEn, borrar: borrarEn };
    dibujarEn(document);
})();
