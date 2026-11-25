// JavaScript mínimo. Sin él, todo sigue funcionando (filtros con el botón "Aplicar",
// contenido visible). Con él, la interfaz es más cómoda:
//   1. Los filtros se aplican al cambiar, SIN recargar la página ni saltar: se pide la página
//      nueva en segundo plano y se sustituye solo la sección del control.
//   2. Las cifras clave se animan al aparecer.
//   3. Los bloques aparecen suavemente al hacer scroll.
//   4. La subnavegación marca la sección que estás viendo.
//   5. Las tablas con data-ordenable se ordenan pulsando la cabecera.
(function () {
    "use strict";
    var reducido = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var formulario = document.getElementById("filtros");

    // 1. Filtros sin recarga ----------------------------------------------------------
    // Qué se sustituye: la sección (<section> dentro de <main>) que contiene el control. Si el
    // control está fuera de una sección (cabecera, subnavegación), afecta a varias secciones y
    // se sustituye todo <main>, pero conservando la posición de la pantalla.
    function clave(seccion) {
        if (seccion.id) { return "#" + CSS.escape(seccion.id); }
        var t = seccion.getAttribute("aria-labelledby");
        return t ? 'section[aria-labelledby="' + t + '"]' : null;
    }

    function zona(control) {
        // data-zona="main": el control afecta a toda la página (p. ej. los años del comparador)
        if (control.dataset.zona === "main") { return document.querySelector("main"); }
        var seccion = control.closest("main section.bloque");
        return seccion && clave(seccion) ? seccion : document.querySelector("main");
    }

    function preparar(raiz, inmediato) {
        // Lo que se sustituye ya estaba a la vista: sin la animación de aparecer (que lo dejaba
        // medio segundo transparente, como si la sección estuviera en blanco)
        raiz.querySelectorAll(".reveal").forEach(function (b) { b.classList.remove("reveal"); });
        if (raiz.classList) { raiz.classList.remove("reveal"); }
        ordenables(raiz);
        if (window.Graficos) { window.Graficos.dibujar(raiz, inmediato); }
    }

    // Si se pulsa otra opción antes de que llegue la respuesta, la petición anterior se cancela:
    // así no se encadenan varias sustituciones seguidas (eso es lo que dejaba la página "pegada").
    var pendiente = null;

    function aplicar(control) {
        var form = document.getElementById("filtros");       // se busca cada vez: puede haberse sustituido
        var url = new URL(form.getAttribute("action") || location.pathname, location.href);
        url.search = new URLSearchParams(new FormData(form)).toString();
        var destino = zona(control);
        var esMain = destino.tagName === "MAIN";
        var selector = esMain ? "main" : clave(destino);
        var scroll = window.scrollY;
        if (pendiente) { pendiente.abort(); }
        var esta = window.AbortController ? new AbortController() : null;
        pendiente = esta;
        destino.classList.add("cargando");
        destino.setAttribute("aria-busy", "true");

        fetch(url, { headers: { "X-Requested-With": "fetch" }, signal: esta ? esta.signal : undefined })
            .then(function (r) { if (!r.ok) { throw new Error(r.status); } return r.text(); })
            .then(function (html) {
                if (pendiente === esta) { pendiente = null; }
                var nuevo = new DOMParser().parseFromString(html, "text/html").querySelector(selector);
                if (!nuevo) { throw new Error("sección no encontrada"); }
                // Guarda qué control tenía el foco para devolvérselo tras el cambio (teclado)
                var nombre = control.name, valor = control.type === "radio" ? control.value : null;
                // La sección nueva conserva la altura de la vieja hasta que sus gráficos están
                // dibujados: así la página no encoge, no salta y no se ve un hueco en blanco.
                var alto = destino.offsetHeight;
                if (window.Graficos) { window.Graficos.borrar(destino); }
                var raiz = destino;
                if (esMain) {
                    destino.innerHTML = nuevo.innerHTML;
                } else {
                    destino.replaceWith(nuevo);
                    raiz = nuevo;
                }
                // al sustituir todo <main> el contenedor es el mismo: hay que quitarle el estado de carga
                raiz.classList.remove("cargando");
                raiz.removeAttribute("aria-busy");
                raiz.style.minHeight = alto + "px";
                // "instant": la página tiene desplazamiento suave y, si la vuelta a la posición se
                // anima, los gráficos se miden con la pantalla a medio camino y no se dibujan
                window.scrollTo({ top: scroll, behavior: "instant" });
                preparar(raiz, esMain ? true : "todos");
                window.scrollTo({ top: scroll, behavior: "instant" });
                requestAnimationFrame(function () { raiz.style.minHeight = ""; });
                history.replaceState(null, "", url.pathname + url.search);
                vigilar();
                var foco = document.querySelector('[name="' + nombre + '"]' + (valor !== null ? '[value="' + valor + '"]' : ""));
                if (foco) { foco.focus({ preventScroll: true }); }
            })
            .catch(function (error) {
                if (error && error.name === "AbortError") {
                    // la ha sustituido una petición más reciente: solo se quita el aviso de carga
                    destino.classList.remove("cargando");
                    destino.removeAttribute("aria-busy");
                    return;
                }
                // Si algo falla, el método de siempre: recargar con el formulario
                form.submit();
            });
    }

    if (formulario && window.fetch && window.DOMParser) {
        // Delegación: funciona también con los controles de las secciones que se sustituyen
        document.addEventListener("change", function (e) {
            var control = e.target.closest("[data-auto]");
            if (control) { aplicar(control); }
        });
    } else if (formulario) {
        document.querySelectorAll("[data-auto]").forEach(function (control) {
            control.addEventListener("change", function () {
                formulario.action = control.dataset.ancla ? "#" + control.dataset.ancla : "";
                formulario.submit();
            });
        });
    }

    // 2. Cifras que "cuentan" hasta su valor ----------------------------------------
    function animarCifra(el) {
        var original = el.textContent.trim();
        var m = original.match(/^([^\d]*)([\d.]+(?:,\d+)?)(.*)$/);
        if (!m) { return; }
        var destino = parseFloat(m[2].replace(/\./g, "").replace(",", "."));
        var decimales = m[2].indexOf(",") >= 0 ? m[2].split(",")[1].length : 0;
        if (isNaN(destino)) { return; }
        var inicio = null, duracion = 900;
        function paso(t) {
            if (inicio === null) { inicio = t; }
            var p = Math.min((t - inicio) / duracion, 1);
            var suave = 1 - Math.pow(1 - p, 3);
            el.textContent = m[1] + (destino * suave).toLocaleString("es-ES", {
                minimumFractionDigits: decimales, maximumFractionDigits: decimales
            }) + m[3];
            if (p < 1) { requestAnimationFrame(paso); } else { el.textContent = original; }
        }
        requestAnimationFrame(paso);
    }

    // 3. Aparición al hacer scroll --------------------------------------------------
    var bloques = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && !reducido) {
        var observador = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (e) {
                if (!e.isIntersecting) { return; }
                e.target.classList.add("visible");
                e.target.querySelectorAll("[data-cuenta]").forEach(animarCifra);
                observador.unobserve(e.target);
            });
        }, { threshold: 0.08, rootMargin: "0px 0px -40px 0px" });
        bloques.forEach(function (b) { observador.observe(b); });
    } else {
        bloques.forEach(function (b) { b.classList.add("visible"); });
    }

    // 5. Tablas ordenables en el navegador (data-ordenable): cada celda lleva su valor en data-v
    function ordenables(raiz) {
        raiz.querySelectorAll("table[data-ordenable]").forEach(function (tabla) {
            var cuerpo = tabla.tBodies[0];
            var estado = { col: -1, desc: true };
            tabla.querySelectorAll("thead th").forEach(function (th, col) {
                var boton = th.querySelector("button");
                if (!boton) { return; }
                boton.addEventListener("click", function () {
                    estado = { col: col, desc: estado.col === col ? !estado.desc : true };
                    var filas = Array.prototype.slice.call(cuerpo.rows);
                    filas.sort(function (a, b) {
                        var x = a.cells[col].dataset.v, y = b.cells[col].dataset.v;
                        if (x === "" && y !== "") { return 1; }          // los vacíos, siempre al final
                        if (y === "" && x !== "") { return -1; }
                        var nx = parseFloat(x), ny = parseFloat(y);
                        var r = (isNaN(nx) || isNaN(ny)) ? String(x).localeCompare(String(y), "es") : nx - ny;
                        return estado.desc ? -r : r;
                    });
                    filas.forEach(function (f) { cuerpo.appendChild(f); });
                    tabla.querySelectorAll("thead th").forEach(function (otro, i) {
                        otro.setAttribute("aria-sort", i === col ? (estado.desc ? "descending" : "ascending") : "none");
                    });
                });
            });
        });
    }
    ordenables(document);

    // 6. Billetes que se rasgan ------------------------------------------------------
    // Al pulsar un [data-rasgar], su talón [data-talon] se arranca por el troquel antes de
    // abrir la página: el borde del billete queda dentado y una copia del talón cae girando.
    // (La copia hace falta porque la máscara de las muescas recortaría el talón al salir.)
    function dientes(ancho, base, alto, haciaArriba) {
        // línea de rotura en zigzag irregular a la altura 'base', de derecha a izquierda
        var puntos = [], x = ancho, i = 0;
        while (x > 0) {
            var y = base + (i % 2 ? 1 : -1) * (2 + Math.random() * alto) * (haciaArriba ? -1 : 1);
            puntos.push(x.toFixed(1) + "px " + y.toFixed(1) + "px");
            x -= 6 + Math.random() * 7;
            i++;
        }
        puntos.push("0px " + base + "px");
        return puntos;
    }

    function rasgar(billete, talon, destino) {
        // se endereza (el :hover lo inclina) para medir en sus propias coordenadas
        billete.style.transition = "none";
        billete.style.transform = "none";
        var ancho = billete.offsetWidth;
        var corte = talon.offsetTop;                           // altura del troquel dentro del billete
        var t = talon.getBoundingClientRect();
        var linea = dientes(ancho, corte, 3, false);

        // el billete se queda sin talón y con el borde roto
        billete.style.clipPath = "polygon(0 0, " + ancho + "px 0, " + linea.join(", ") + ")";
        billete.classList.add("rasgado");

        // la copia del talón, con el borde roto complementario, que cae
        var suelto = talon.cloneNode(true);
        var estilo = getComputedStyle(billete);
        var estiloTalon = getComputedStyle(talon);
        var velo = estiloTalon.backgroundColor;
        suelto.className = talon.className + " talon-suelto";
        suelto.removeAttribute("data-talon");
        Object.assign(suelto.style, {
            left: t.left + "px", top: t.top + "px", width: t.width + "px", height: t.height + "px",
            // fuera del billete no hereda sus variables: se copian el relleno y el color reales
            paddingLeft: estiloTalon.paddingLeft, paddingRight: estiloTalon.paddingRight,
            color: estiloTalon.color,
            background: "linear-gradient(" + velo + "," + velo + "), " + estilo.backgroundColor,
            clipPath: "polygon(" + dientes(t.width, 0, 3, true).reverse().join(", ") + ", " +
                t.width + "px " + t.height + "px, 0px " + t.height + "px)"
        });
        document.body.appendChild(suelto);

        billete.animate([{ transform: "none" }, { transform: "translateY(-3px) rotate(-.6deg)" }, { transform: "none" }],
            { duration: 220, easing: "ease-out" });
        var caida = suelto.animate([
            { transform: "none", opacity: 1 },
            { transform: "translate(4px, 3px) rotate(2deg)", opacity: 1, offset: 0.22 },
            { transform: "translate(46px, 170px) rotate(19deg)", opacity: 0 }
        ], { duration: 700, easing: "cubic-bezier(.45, 0, .8, .4)", fill: "forwards" });
        caida.finished.then(function () { location.href = destino; });
    }

    document.addEventListener("click", function (e) {
        var billete = e.target.closest("[data-rasgar]");
        if (!billete || billete.classList.contains("rasgado")) { return; }
        // abrir en otra pestaña o ventana: comportamiento normal
        if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) { return; }
        var talon = billete.querySelector("[data-talon]");
        if (!talon || reducido || !billete.animate) { return; }
        e.preventDefault();
        rasgar(billete, talon, billete.href);
    });

    // La entrada de la portada (las fechas): el talón está a la derecha, así que el corte es
    // vertical. No abre nada: el talón cae y, poco después, vuelve a su sitio.
    function dientesV(alto, x, amplitud, haciaIzquierda) {
        // línea de rotura vertical en zigzag a la distancia 'x', de arriba abajo
        var puntos = [], y = 0, i = 0;
        while (y < alto) {
            var dx = (i % 2 ? 1 : -1) * (1 + Math.random() * amplitud) * (haciaIzquierda ? -1 : 1);
            puntos.push((x + dx).toFixed(1) + "px " + y.toFixed(1) + "px");
            y += 4 + Math.random() * 4;
            i++;
        }
        puntos.push(x + "px " + alto + "px");
        return puntos;
    }

    function rasgarEntrada(entrada) {
        var cuerpo = entrada.querySelector(".entrada__cuerpo");
        var talon = entrada.querySelector(".entrada__talon");
        if (!cuerpo || !talon || entrada.classList.contains("rasgado")) { return; }
        var w = cuerpo.offsetWidth, h = cuerpo.offsetHeight;
        var tw = talon.offsetWidth, th = talon.offsetHeight;
        var caja = talon.getBoundingClientRect();
        var giro = getComputedStyle(entrada).transform;          // la entrada está algo inclinada

        // el cuerpo se queda con el borde derecho roto
        cuerpo.style.clipPath = "polygon(0 0, " + dientesV(h, w - 1, 2.5, true).join(", ") + ", 0 " + h + "px)";
        entrada.classList.add("rasgado");

        // la copia del talón, con el borde izquierdo roto, cae girando
        var suelto = talon.cloneNode(true);
        suelto.classList.add("entrada__talon--suelto");
        Object.assign(suelto.style, {
            left: (caja.left + caja.width / 2 - tw / 2) + "px", top: (caja.top + caja.height / 2 - th / 2) + "px",
            width: tw + "px", height: th + "px", transform: giro === "none" ? "" : giro,
            clipPath: "polygon(" + dientesV(th, 1, 2.5, false).reverse().join(", ") + ", " + tw + "px 0, " + tw + "px " + th + "px)"
        });
        document.body.appendChild(suelto);

        entrada.animate([{ transform: giro }, { transform: giro + " translateX(-3px) rotate(-1deg)" }, { transform: giro }],
            { duration: 240, easing: "ease-out" });
        suelto.animate([
            { transform: giro, opacity: 1 },
            { transform: giro + " translate(6px, 2px) rotate(4deg)", opacity: 1, offset: 0.2 },
            { transform: giro + " translate(60px, 190px) rotate(34deg)", opacity: 0 }
        ], { duration: 900, easing: "cubic-bezier(.45, 0, .8, .4)", fill: "forwards" }).finished.then(function () {
            suelto.remove();
            // al rato, entrada nueva: el talón vuelve a aparecer en su sitio
            setTimeout(function () {
                cuerpo.style.clipPath = "";
                entrada.classList.remove("rasgado");
                talon.animate([{ opacity: 0, transform: "translateX(10px)" }, { opacity: 1, transform: "none" }],
                    { duration: 380, easing: "ease-out" });
            }, 900);
        });
    }

    document.querySelectorAll("[data-rasgar-entrada]").forEach(function (entrada) {
        entrada.addEventListener("click", function () {
            if (!reducido && entrada.animate) { rasgarEntrada(entrada); }
        });
    });

    // Al volver con "atrás", el navegador puede restaurar la página tal cual: billetes enteros otra vez
    window.addEventListener("pageshow", function (e) {
        if (!e.persisted) { return; }
        document.querySelectorAll(".talon-suelto").forEach(function (s) { s.remove(); });
        document.querySelectorAll("[data-rasgar].rasgado").forEach(function (b) {
            b.classList.remove("rasgado");
            b.style.clipPath = b.style.transform = b.style.transition = "";
        });
    });

    // 4. Subnavegación: marca la sección visible --------------------------------------
    var enlaces = document.querySelectorAll(".subnav a[href^='#']");
    var secciones = [];
    enlaces.forEach(function (a) {
        var destino = document.getElementById(a.getAttribute("href").slice(1));
        if (destino) { secciones.push({ enlace: a, id: destino.id }); }
    });
    var espia = null;
    function vigilar() {
        if (!secciones.length || !("IntersectionObserver" in window)) { return; }
        if (espia) { espia.disconnect(); }
        var activa = null;
        espia = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (e) { if (e.isIntersecting) { activa = e.target.id; } });
            secciones.forEach(function (s) { s.enlace.classList.toggle("visible", s.id === activa); });
        }, { rootMargin: "-30% 0px -60% 0px" });
        // Se buscan de nuevo por id: tras sustituir una sección, los elementos son otros
        secciones.forEach(function (s) {
            var el = document.getElementById(s.id);
            if (el) { espia.observe(el); }
        });
    }
    vigilar();
})();
