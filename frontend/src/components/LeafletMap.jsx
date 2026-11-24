import { useEffect, useRef } from 'react';
import { KELAS_COLOR } from '../constants';


import { cn } from '../utils';





let cachedPosition = null;





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





const TILE_PROVIDERS = {


  osm: {


    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',


    options: {


      maxZoom: 19,


      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',


    },


  },


  topo: {


    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',


    options: {


      maxZoom: 17,


      attribution: '&copy; OpenStreetMap, SRTM | &copy; OpenTopoMap',


    },


  },


  satellite: {


    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',


    options: {


      maxZoom: 18,


      attribution: '&copy; Esri, Maxar, Earthstar Geographics',


    },


  },


};





const DIRECTION_ID = {


  N: 'utara',


  NE: 'timur laut',


  E: 'timur',


  SE: 'tenggara',


  S: 'selatan',


  SW: 'barat daya',


  W: 'barat',


  NW: 'barat laut',


};





function translateTurnInstruction(instr) {


  if (!instr) return 'Lanjutkan perjalanan';


  const road = instr.road ? ` di ${instr.road}` : '';


  const dir = DIRECTION_ID[instr.direction] || instr.direction || '';


  switch (instr.type) {


    case 'Head':


    case 'StartAt':


      return `Mulai ke arah ${dir || 'depan'}${road}`;


    case 'Continue':


      return `Lurus terus${dir ? ` ke arah ${dir}` : ''}${road}`;


    case 'SlightRight':


      return `Serong ke kanan${road}`;


    case 'Right':


      return `Belok kanan${road}`;


    case 'SharpRight':


      return `Belok kanan tajam${road}`;


    case 'SlightLeft':


      return `Serong ke kiri${road}`;


    case 'Left':


      return `Belok kiri${road}`;


    case 'SharpLeft':


      return `Belok kiri tajam${road}`;


    case 'TurnAround':


      return `Putar balik${road}`;


    case 'Roundabout':


      return `Masuk bundaran${road}`;


    case 'DestinationReached':


    case 'WaypointReached':


      return 'Anda telah tiba di lokasi tujuan';


    default:


      return instr.text || `Lanjutkan${road}`;


  }


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


  wrap.className = 'w-[235px] font-sans';





  if (hospital.foto) {


    const img = document.createElement('img');


    img.src = hospital.foto;


    img.alt = hospital.nama;


    img.loading = 'lazy';


    img.className = 'mb-2 h-24 w-full rounded-lg object-cover';


    img.onerror = () => img.remove();


    wrap.appendChild(img);


  }





  const badgeRow = document.createElement('div');


  badgeRow.className = 'mb-1 flex items-center gap-1';


  const kBadge = document.createElement('span');


  kBadge.className = 'rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-700';


  kBadge.textContent = `Kelas ${hospital.kelas || '—'}`;


  badgeRow.appendChild(kBadge);





  if (hospital.bpjs) {


    const bBadge = document.createElement('span');


    bBadge.className = 'rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700';


    bBadge.textContent = 'BPJS';


    badgeRow.appendChild(bBadge);


  }


  wrap.appendChild(badgeRow);





  const name = document.createElement('h3');


  name.className = 'text-[13px] font-bold leading-snug text-slate-900';


  name.textContent = hospital.nama;


  wrap.appendChild(name);





  const meta = document.createElement('p');


  meta.className = 'mt-0.5 text-[11px] text-slate-500';


  meta.textContent = `${hospital.jenis || 'Rumah sakit'} • ${hospital.kabkota || 'Sumatera Utara'}`;


  wrap.appendChild(meta);





  const actions = document.createElement('div');


  actions.className = 'mt-2.5 flex items-center gap-1.5';





  if (onSelect) {


    const button = document.createElement('button');


    button.type = 'button';


    button.className =


      'flex-1 rounded-full bg-toba px-3 py-1.5 text-[11px] font-bold text-white transition hover:bg-toba-dark';


    button.textContent = 'Pilih di Peta';


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


  onMapMovingChange,


  hospitals = [],


  selectedId = null,


  onSelect = null,


  fit = true,


  className = '',


  center = [3.55, 98.65],


  zoom = 8,


  showZoom = true,


  showLocate = true,


  tileMode = 'osm',


  userLocation = null,


  radiusKm = null,


  referralLinks = [],


  routeTarget = null,


  routeMode = 'driving',


  onRouteInfo = null,


  onRouteError = null,


  onLocate = null,


  onUserViewportChange = null,


}) {


  const containerRef = useRef(null);


  const mapRef = useRef(null);


  const tileLayerRef = useRef(null);


  const layerRef = useRef(null);


  const radiusLayerRef = useRef(null);


  const referralLayerRef = useRef(null);


  const markerMapRef = useRef(new Map());


  const routingRef = useRef(null);


  const userInteractingRef = useRef(false);


  const callbacksRef = useRef({


    onSelect,


    onRouteInfo,


    onRouteError,


    onLocate,


    onUserViewportChange,


  });


  callbacksRef.current = {


    onSelect,


    onRouteInfo,


    onRouteError,


    onLocate,


    onUserViewportChange,


  };





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





    const initialProvider = TILE_PROVIDERS[tileMode] || TILE_PROVIDERS.osm;


    tileLayerRef.current = L.tileLayer(initialProvider.url, initialProvider.options).addTo(map);





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





    radiusLayerRef.current = L.layerGroup().addTo(map);


    referralLayerRef.current = L.layerGroup().addTo(map);





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





    // Deteksi geser/zoom manual oleh pengguna


    const markUserAction = () => {


      userInteractingRef.current = true;


    };


    const emitViewport = () => {


      if (!userInteractingRef.current) return;


      userInteractingRef.current = false;


      const b = map.getBounds();


      callbacksRef.current.onUserViewportChange?.({


        south: b.getSouth(),


        west: b.getWest(),


        north: b.getNorth(),


        east: b.getEast(),


      });


    };





    map.on('dragstart', markUserAction);


    map.on('moveend', emitViewport);





    const containerEl = containerRef.current;


    const onWheel = () => {


      userInteractingRef.current = true;


    };


    containerEl?.addEventListener('wheel', onWheel, { passive: true });


    containerEl?.addEventListener('touchstart', onWheel, { passive: true });





    const invalidateSizeTimer = window.setTimeout(() => map.invalidateSize(), 120);





    return () => {


      window.clearTimeout(invalidateSizeTimer);


      containerEl?.removeEventListener('wheel', onWheel);


      containerEl?.removeEventListener('touchstart', onWheel);


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


      tileLayerRef.current = null;


      layerRef.current = null;


      radiusLayerRef.current = null;


      referralLayerRef.current = null;


      markerMapRef.current = new Map();


    };


    // eslint-disable-next-line react-hooks/exhaustive-deps


  }, []);





  // Switch tile layer dynamically (osm / topo / satellite)


  useEffect(() => {


    const L = window.L;


    const map = mapRef.current;


    if (!L || !map) return;





    if (tileLayerRef.current) {


      map.removeLayer(tileLayerRef.current);


    }


    const provider = TILE_PROVIDERS[tileMode] || TILE_PROVIDERS.osm;


    tileLayerRef.current = L.tileLayer(provider.url, provider.options).addTo(map);


    tileLayerRef.current.bringToBack();


  }, [tileMode]);





  // Draw user location & radius circle when active


  useEffect(() => {


    const L = window.L;


    const map = mapRef.current;


    const rLayer = radiusLayerRef.current;


    if (!L || !map || !rLayer) return;





    rLayer.clearLayers();


    if (!userLocation || userLocation.length !== 2) return;





    L.marker(userLocation, {


      icon: L.divIcon({


        className: '',


        html: '<div class="carisehat-origin"></div>',


        iconSize: [18, 18],


        iconAnchor: [9, 9],


      }),


      interactive: false,


    }).addTo(rLayer);





    if (radiusKm && Number(radiusKm) > 0) {


      const circle = L.circle(userLocation, {


        radius: Number(radiusKm) * 1000,


        color: '#0F766E',


        weight: 2,


        dashArray: '6 6',


        fillColor: '#0F766E',


        fillOpacity: 0.08,


      }).addTo(rLayer);


      map.fitBounds(circle.getBounds(), { padding: [30, 30] });


    }


  }, [userLocation, radiusKm]);





  // Draw Referral Network Polylines (Rujukan Berjenjang BPJS)


  useEffect(() => {


    const L = window.L;


    const map = mapRef.current;


    const refLayer = referralLayerRef.current;


    if (!L || !map || !refLayer) return;





    refLayer.clearLayers();


    if (!referralLinks || !referralLinks.length) return;





    const allPoints = [];


    referralLinks.forEach((link, idx) => {


      if (!link.from || !link.to) return;


      allPoints.push(link.from, link.to);


      const color = idx === 0 ? '#0F766E' : '#D97706';





      L.polyline([link.from, link.to], {


        color,


        weight: 4,


        opacity: 0.9,


        dashArray: '8 8',


      }).addTo(refLayer);





      L.circleMarker(link.to, {


        radius: 14,


        color,


        weight: 2.5,


        fillColor: color,


        fillOpacity: 0.16,


      })


        .bindTooltip(`${link.tierLabel}: ${link.target?.nama || ''}`, {


          permanent: false,


          direction: 'top',


        })


        .addTo(refLayer);


    });





    if (allPoints.length >= 2) {


      map.fitBounds(allPoints, { padding: [60, 60], maxZoom: 12 });


    }


  }, [referralLinks]);





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


      marker.bindPopup(popupElement(hospital, callbacksRef.current.onSelect), {


        maxWidth: 260,


        minWidth: 225,


      });


      marker.on('click', () => callbacksRef.current.onSelect?.(hospital));


      layer.addLayer(marker);


      markerMapRef.current.set(hospital.id, marker);


    });





    if (selectedId && markerMapRef.current.has(selectedId) && !referralLinks.length) {


      const marker = markerMapRef.current.get(selectedId);


      if (layer.zoomToShowLayer) layer.zoomToShowLayer(marker, () => marker.openPopup());


      else marker.openPopup();


    }





    if (fit && !radiusKm && !referralLinks.length && hospitals.length) {


      const points = hospitals.filter((h) => h.lat != null && h.lon != null).map((h) => [h.lat, h.lon]);


      if (points.length === 1) map.setView(points[0], 13);


      else if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 12 });


    }


  }, [hospitals, selectedId, fit, radiusKm, referralLinks.length]);





  useEffect(() => {


    const map = mapRef.current;


    if (!map || !selectedId || referralLinks.length) return;


    const hospital = hospitals.find((item) => item.id === selectedId);


    if (hospital?.lat != null && hospital?.lon != null) {


      map.flyTo([hospital.lat, hospital.lon], Math.max(map.getZoom(), 13), { duration: 0.7 });


    }


  }, [selectedId, hospitals, referralLinks.length]);





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


          show: false,


          lineOptions: {


            styles: [


              { color: '#ffffff', opacity: 0.95, weight: 11 },


              { color: '#0F766E', opacity: 1, weight: 6 },


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


          const steps = (route?.instructions || []).map((inst, idx) => ({


            step: idx + 1,


            instruction: translateTurnInstruction(inst),


            distance: inst.distance,


            time: inst.time,


          }));


          if (summary) {


            callbacksRef.current.onRouteInfo?.({


              distance: summary.totalDistance,


              time: summary.totalTime,


              mode: routeMode,


              origin: position,


              destination: [routeTarget.lat, routeTarget.lon],


              steps,


            });


          }


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





  


  useEffect(() => {


    const map = mapRef?.current || instanceRef?.current;


    if (!map || typeof map.on !== 'function' || !onMapMovingChange) return undefined;


    let timer = null;


    const handleStart = () => {


      if (timer) window.clearTimeout(timer);


      onMapMovingChange(true);


    };


    const handleEnd = () => {


      if (timer) window.clearTimeout(timer);


      timer = window.setTimeout(() => onMapMovingChange(false), 750);


    };


    map.on('dragstart movestart zoomstart', handleStart);


    map.on('dragend moveend zoomend', handleEnd);


    return () => {


      if (timer) window.clearTimeout(timer);


      map.off('dragstart movestart zoomstart', handleStart);


      map.off('dragend moveend zoomend', handleEnd);


    };


  }, [onMapMovingChange]);





  return (


    <div


      ref={containerRef}


      className={cn("isolate overflow-hidden", 'z-0 h-full w-full bg-[#eaf5f3]', className)}


      role="application"


      aria-label="Peta persebaran rumah sakit"


    />


  );


}


