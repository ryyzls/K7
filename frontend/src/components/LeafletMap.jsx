import { useEffect, useRef } from 'react';
import { KELAS_COLOR } from '../constants';
import { cn } from '../utils';

let cachedPosition = null;

export function translateInstruction(text) {
  if (!text) return 'Lanjut di rute';
  return text
    .replace(/^Head\s+northwest/i, 'Mulai ke arah barat laut')
    .replace(/^Head\s+northeast/i, 'Mulai ke arah timur laut')
    .replace(/^Head\s+southwest/i, 'Mulai ke arah barat daya')
    .replace(/^Head\s+southeast/i, 'Mulai ke arah tenggara')
    .replace(/^Head\s+north/i, 'Mulai ke arah utara')
    .replace(/^Head\s+south/i, 'Mulai ke arah selatan')
    .replace(/^Head\s+east/i, 'Mulai ke arah timur')
    .replace(/^Head\s+west/i, 'Mulai ke arah barat')
    .replace(/^Head/i, 'Mulai perjalanan')
    .replace(/^Turn\s+sharp\s+right/i, 'Belok kanan tajam')
    .replace(/^Turn\s+sharp\s+left/i, 'Belok kiri tajam')
    .replace(/^Turn\s+slight\s+right/i, 'Serong kanan')
    .replace(/^Turn\s+slight\s+left/i, 'Serong kiri')
    .replace(/^Turn\s+right/i, 'Belok kanan')
    .replace(/^Turn\s+left/i, 'Belok kiri')
    .replace(/^Make\s+a\s+U-turn/i, 'Putar balik')
    .replace(/^Continue/i, 'Lurus terus')
    .replace(/^Keep\s+right/i, 'Tetap di lajur kanan')
    .replace(/^Keep\s+left/i, 'Tetap di lajur kiri')
    .replace(/\bonto\b/gi, 'ke')
    .replace(/\bon\b/gi, 'di')
    .replace(/You have arrived at your destination/gi, 'Anda telah tiba di tujuan')
    .replace(/Destination reached/gi, 'Anda telah tiba di tujuan')
    .replace(/Take the (\d+)[a-z]* exit/gi, 'Ambil jalan keluar ke-$1')
    .replace(/At the roundabout/gi, 'Di bundaran')
    .replace(/\s+towards\s+/gi, ' menuju ')
    .replace(/\s+to\s+/gi, ' ke ');
}

export function getUserPosition({ timeout = 10000 } = {}) {
  if (cachedPosition) return Promise.resolve(cachedPosition);
  if (!navigator.geolocation) {
    return Promise.reject(new Error('Browser tidak mendukung deteksi lokasi.'));
  }
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        cachedPosition = [position.coords.latitude, position.coords.longitude];
        resolve(cachedPosition);
      },
      (error) => {
        const message =
          error.code === 1
            ? 'Izin lokasi ditolak. Aktifkan akses GPS pada browser Anda.'
            : 'Lokasi Anda belum dapat ditentukan. Coba lagi.';
        reject(new Error(message));
      },
      { enableHighAccuracy: true, timeout },
    );
  });
}

function pinHtml(hospital, active) {
  const color = KELAS_COLOR[hospital.kelas] || '#64748B';
  return `<div class="carisehat-pin${active ? ' is-active' : ''}" style="--pin:${color}">
    <span class="carisehat-pin__pulse"></span>
    <span class="carisehat-pin__body"><span class="material-symbols-outlined">local_hospital</span></span>
    <span class="carisehat-pin__tip"></span>
  </div>`;
}

function popupElement(hospital, onSelect) {
  const wrap = document.createElement('article');
  wrap.className = 'w-[228px] font-body';

  if (hospital.foto) {
    const img = document.createElement('img');
    img.src = hospital.foto;
    img.alt = hospital.nama;
    img.loading = 'lazy';
    img.className = 'mb-2 h-24 w-full rounded-lg object-cover';
    img.onerror = () => img.remove();
    wrap.appendChild(img);
  }

  const name = document.createElement('h3');
  name.className = 'font-heading text-[13px] font-bold leading-snug text-slate-900';
  name.textContent = hospital.nama;
  wrap.appendChild(name);

  const meta = document.createElement('p');
  meta.className = 'mt-0.5 text-[11px] text-slate-500';
  meta.textContent = `${hospital.jenis || 'Rumah sakit'} • ${hospital.kabkota || 'Sumatera Utara'}`;
  wrap.appendChild(meta);

  const actions = document.createElement('div');
  actions.className = 'mt-2 flex items-center gap-1.5';

  if (onSelect) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className =
      'flex-1 rounded-full bg-brand-blue px-3 py-1.5 text-[11px] font-semibold text-white transition hover:bg-brand-navy';
    button.textContent = 'Lihat detail';
    button.onclick = () => onSelect(hospital);
    actions.appendChild(button);
  }

  const link = document.createElement('a');
  link.href = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;
  link.className =
    'flex-1 rounded-full border border-slate-300 px-3 py-1.5 text-center text-[11px] font-semibold text-slate-700 transition hover:bg-slate-50';
  link.textContent = 'Profil';
  actions.appendChild(link);

  wrap.appendChild(actions);
  return wrap;
}

export default function LeafletMap({
  hospitals = [],
  selectedId = null,
  onSelect = null,
  fit = true,
  className = '',
  center = [3.55, 98.65],
  zoom = 8,
  showZoom = true,
  showLocate = true,
  showPopup = true,
  routeTarget = null,
  routeMode = 'driving',
  onRouteInfo = null,
  onRouteError = null,
  onLocate = null,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const markerMapRef = useRef(new Map());
  const routingRef = useRef(null);
  const callbacksRef = useRef({ onSelect, onRouteInfo, onRouteError, onLocate });
  callbacksRef.current = { onSelect, onRouteInfo, onRouteError, onLocate };

  useEffect(() => {
    if (!containerRef.current || mapRef.current || !window.L) return undefined;
    const L = window.L;

    const map = L.map(containerRef.current, {
      center,
      zoom,
      zoomControl: false,
      scrollWheelZoom: true,
    });
    mapRef.current = map;

    // Google Maps Road (Layanan default - sangat stabil, cepat, dan tidak terblokir di ISP Indonesia)
    const gmRoadLayer = L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
      subdomains: ['0', '1', '2', '3'],
      maxZoom: 20,
      attribution: '&copy; <a href="https://maps.google.com">Google Maps</a>',
    });

    // CARTO Voyager (Tile cepat & stabil)
    const cartoLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      subdomains: 'abcd',
      maxZoom: 19,
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    });

    // OpenStreetMap
    const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    });

    // Google Maps Satelit
    const gmSatLayer = L.tileLayer('https://mt{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
      subdomains: ['0', '1', '2', '3'],
      maxZoom: 20,
      attribution: '&copy; <a href="https://maps.google.com">Google Maps</a>',
    });

    // Set Google Maps as active layer by default to prevent white/blank tile dropouts
    gmRoadLayer.addTo(map);

    const baseMaps = {
      'Google Maps': gmRoadLayer,
      'Peta Voyager': cartoLayer,
      'OpenStreetMap': osmLayer,
      'Google Satelit': gmSatLayer,
    };

    L.control.layers(baseMaps, {}, { position: 'topright', collapsed: true }).addTo(map);

    if (showZoom) {
      L.control.zoom({ position: 'topright' }).addTo(map);
    }

    if (showLocate && L.control.locate) {
      L.control
        .locate({
          position: 'topright',
          flyTo: true,
          strings: { title: 'Cari lokasi saya' },
          locateOptions: { enableHighAccuracy: true },
          onLocationError: () => {
            callbacksRef.current.onLocate?.(null, new Error('Lokasi tidak dapat ditemukan.'));
          },
          onLocationOutsideMapBounds: () => {},
        })
        .addTo(map);
      map.on('locationfound', (event) => {
        callbacksRef.current.onLocate?.([event.latitude, event.longitude], null);
      });
    }

    layerRef.current = L.markerClusterGroup
      ? L.markerClusterGroup({
          showCoverageOnHover: false,
          maxClusterRadius: 46,
          iconCreateFunction: (cluster) => {
            const count = cluster.getChildCount();
            return L.divIcon({
              html: `<div class="carisehat-cluster">${count}</div>`,
              className: 'carisehat-cluster-wrap',
              iconSize: [38, 38],
            });
          },
        })
      : L.layerGroup();
    layerRef.current.addTo(map);

    window.setTimeout(() => map.invalidateSize(), 120);

    return () => {
      if (routingRef.current) {
        try {
          map.removeControl(routingRef.current);
        } catch {
          /* already removed */
        }
        routingRef.current = null;
      }
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
      markerMapRef.current = new Map();
    };
    // Map is created once; props below are applied by the other effects.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Draw hospital markers whenever the filtered collection changes.
  useEffect(() => {
    const L = window.L;
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!L || !map || !layer) return;

    layer.clearLayers();
    markerMapRef.current = new Map();

    hospitals.forEach((hospital) => {
      if (hospital.lat == null || hospital.lon == null) return;
      const active = hospital.id === selectedId;
      const marker = L.marker([hospital.lat, hospital.lon], {
        icon: L.divIcon({
          html: pinHtml(hospital, active),
          className: 'carisehat-pin-wrap',
          iconSize: active ? [40, 52] : [32, 42],
          iconAnchor: active ? [20, 52] : [16, 42],
          popupAnchor: [0, active ? -48 : -38],
        }),
        title: hospital.nama,
        zIndexOffset: active ? 1000 : 0,
      });
      if (!routeTarget && showPopup) {
        marker.bindPopup(popupElement(hospital, callbacksRef.current.onSelect), {
          maxWidth: 250,
          minWidth: 220,
        });
      }
      marker.on('click', () => callbacksRef.current.onSelect?.(hospital));
      layer.addLayer(marker);
      markerMapRef.current.set(hospital.id, marker);
    });

    if (!routeTarget && showPopup && selectedId && markerMapRef.current.has(selectedId)) {
      const marker = markerMapRef.current.get(selectedId);
      if (layer.zoomToShowLayer) layer.zoomToShowLayer(marker, () => marker.openPopup());
      else marker.openPopup();
    }

    if (fit && hospitals.length) {
      const points = hospitals.filter((h) => h.lat != null && h.lon != null).map((h) => [h.lat, h.lon]);
      if (points.length === 1) map.setView(points[0], 13);
      else if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 12 });
    }
  }, [hospitals, selectedId, fit]);

  // Re-center when a page asks for a specific hospital.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedId) return;
    const hospital = hospitals.find((item) => item.id === selectedId);
    if (hospital?.lat != null && hospital?.lon != null) {
      map.flyTo([hospital.lat, hospital.lon], Math.max(map.getZoom(), 13), { duration: 0.7 });
    }
  }, [selectedId, hospitals]);

  // Build/clear an OSRM route from the visitor's GPS position.
  useEffect(() => {
    const L = window.L;
    const map = mapRef.current;
    if (!L || !map) return undefined;

    if (routingRef.current) {
      try {
        map.removeControl(routingRef.current);
      } catch {
        /* noop */
      }
      routingRef.current = null;
    }

    if (!routeTarget || routeTarget.lat == null || routeTarget.lon == null) return undefined;

    let cancelled = false;
    getUserPosition()
      .then((position) => {
        if (cancelled) return;

        if (L.Routing) {
          L.Routing.Localization = L.Routing.Localization || {};
          L.Routing.Localization.id = {
            directions: {
              N: 'utara',
              NE: 'timur laut',
              E: 'timur',
              SE: 'tenggara',
              S: 'selatan',
              SW: 'barat daya',
              W: 'barat',
              NW: 'barat laut',
            },
            instructions: {
              Head: ['Mulai ke arah {dir}', ' di {road}'],
              Continue: ['Lurus ke arah {dir}', ' di {road}'],
              SlightRight: ['Serong kanan', ' ke {road}'],
              Right: ['Belok kanan', ' ke {road}'],
              SharpRight: ['Belok kanan tajam', ' ke {road}'],
              TurnAround: ['Putar balik'],
              SharpLeft: ['Belok kiri tajam', ' ke {road}'],
              Left: ['Belok kiri', ' ke {road}'],
              SlightLeft: ['Serong kiri', ' ke {road}'],
              WaypointReached: ['Titik tujuan tercapai'],
              Roundabout: ['Ambil bundaran, keluar ke-{exit}', ' menuju {road}'],
              DestinationReached: ['Anda telah tiba di tujuan'],
              Fork: ['Di pertigaan, ambil arah {modifier}', ' menuju {road}'],
              Merge: ['Bergabung ke arah {modifier}', ' ke {road}'],
              OnRamp: ['Masuk jalur ke arah {modifier}', ' menuju {road}'],
              OffRamp: ['Keluar jalur ke arah {modifier}', ' menuju {road}'],
              EndOfRoad: ['Di ujung jalan, belok {modifier}', ' ke {road}'],
              Onto: ['Masuk ke {road}'],
            },
            formatOrder: (n) => String(n),
            ui: {
              startPlaceholder: 'Lokasi Anda',
              viaPlaceholder: 'Via {viaNumber}',
              endPlaceholder: 'Rumah sakit',
            },
          };
        }

        const router =
          routeMode === 'foot' && L.Routing?.osrmv1
            ? L.Routing.osrmv1({
                serviceUrl: 'https://routing.openstreetmap.de/routed-foot/route/v1',
                profile: 'foot',
                timeout: 15000,
              })
            : L.Routing?.osrmv1
              ? L.Routing.osrmv1({
                  serviceUrl: 'https://router.project-osrm.org/route/v1',
                  profile: 'driving',
                  timeout: 15000,
                })
              : undefined;

        const control = L.Routing.control({
          ...(router ? { router } : {}),
          waypoints: [L.latLng(position[0], position[1]), L.latLng(routeTarget.lat, routeTarget.lon)],
          routeWhileDragging: false,
          addWaypoints: false,
          draggableWaypoints: false,
          fitSelectedRoutes: true,
          showAlternatives: false,
          language: 'id',
          show: false,
          lineOptions: {
            styles: [
              { color: '#ffffff', opacity: 0.95, weight: 11 },
              { color: '#0057B8', opacity: 1, weight: 6 },
              { color: '#ffffff', opacity: 0.55, weight: 1.5, dashArray: '1 12' },
            ],
            extendToWaypoints: true,
            missingRouteTolerance: 0,
          },
          createMarker: (index, waypoint) =>
            L.marker(waypoint.latLng, {
              icon: L.divIcon({
                className: '',
                html:
                  index === 0
                    ? '<div class="carisehat-origin"></div>'
                    : '<div class="carisehat-destination"><span class="material-symbols-outlined">local_hospital</span></div>',
                iconSize: index === 0 ? [18, 18] : [36, 36],
                iconAnchor: index === 0 ? [9, 9] : [18, 36],
              }),
              interactive: false,
            }),
        }).addTo(map);

        routingRef.current = control;

        control.on('routesfound', (event) => {
          if (cancelled) return;
          const route = event.routes?.[0];
          const summary = route?.summary;
          const formatter = control.getFormatter ? control.getFormatter() : (L.Routing?.Formatter ? new L.Routing.Formatter({ language: 'id' }) : null);
          const rawInstructions = route?.instructions || [];
          const instructions = rawInstructions.map((step) => {
            let txt = '';
            if (formatter?.formatInstruction) {
              try {
                txt = formatter.formatInstruction(step);
              } catch {
                txt = step.text || step.road || '';
              }
            } else {
              txt = step.text || step.road || '';
            }
            return {
              text: translateInstruction(txt),
              distance: step.distance,
              time: step.time,
              type: step.type,
              modifier: step.modifier,
            };
          });
          if (summary) {
            callbacksRef.current.onRouteInfo?.({
              distance: summary.totalDistance,
              time: summary.totalTime,
              mode: routeMode,
              origin: position,
              destination: [routeTarget.lat, routeTarget.lon],
              instructions,
            });
          }
          window.setTimeout(() => {
            try {
              map.invalidateSize();
            } catch {
              /* noop */
            }
          }, 150);
        });

        control.on('routingerror', () => {
          if (cancelled) return;
          callbacksRef.current.onRouteError?.(new Error('Rute belum dapat dihitung. Coba lagi beberapa saat.'));
        });
      })
      .catch((error) => {
        if (cancelled) return;
        callbacksRef.current.onRouteError?.(error);
      });

    return () => {
      cancelled = true;
    };
  }, [routeTarget, routeMode]);

  return (
    <div
      ref={containerRef}
      className={cn('z-0 h-full w-full bg-[#eaf1f7]', className)}
      style={{ width: '100%', height: '100%' }}
      role="application"
      aria-label="Peta persebaran rumah sakit"
    />
  );
}
