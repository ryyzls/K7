import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  addFavoriteRs,
  getPatientDashboard,
  loginPatient,
  logoutPatient,
  registerPatient,
  removeFavoriteRs,
} from '../api';

const AppContext = createContext(null);

const USER_KEY = 'carisehat_user';
const TOKEN_KEY = 'carisehat_token';
const FAVORITES_KEY = 'carisehat_favorites';

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => readStorage(USER_KEY, null));
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(TOKEN_KEY) || '';
    } catch {
      return '';
    }
  });
  const [loginOpen, setLoginOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [favorites, setFavorites] = useState(() => readStorage(FAVORITES_KEY, []));

  useEffect(() => {
    try {
      if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
      else localStorage.removeItem(USER_KEY);
    } catch {
      /* ignore */
    }
  }, [user]);

  useEffect(() => {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  }, [token]);

  useEffect(() => {
    try {
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
    } catch {
      /* ignore */
    }
  }, [favorites]);

  const toast = useCallback((message, tone = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, 4200);
  }, []);

  const syncServerFavorites = useCallback(async (activeToken) => {
    if (!activeToken) return;
    try {
      const dash = await getPatientDashboard(activeToken);
      if (dash?.profil) setUser(dash.profil);
      if (Array.isArray(dash?.favorit_rs)) {
        setFavorites(dash.favorit_rs.map((item) => item.rs_id));
      }
    } catch (err) {
      if (err.status === 401) {
        setToken('');
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    if (token) syncServerFavorites(token);
  }, [token, syncServerFavorites]);

  const openLogin = useCallback(() => setLoginOpen(true), []);
  const closeLogin = useCallback(() => setLoginOpen(false), []);

  const login = useCallback(
    async (usernameOrEmail, password) => {
      const res = await loginPatient({
        username_or_email: usernameOrEmail,
        password,
      });
      setToken(res.access_token);
      setUser(res.user);
      setLoginOpen(false);
      toast(`Selamat datang, ${res.user.nama_lengkap}!`, 'success');
      return res;
    },
    [toast],
  );

  const registerAndLogin = useCallback(
    async (payload) => {
      await registerPatient(payload);
      return login(payload.username, payload.password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    const currentToken = token;
    setToken('');
    setUser(null);
    setFavorites([]);
    if (currentToken) {
      logoutPatient(currentToken).catch(() => {});
    }
    toast('Anda telah keluar dari akun pasien.', 'info');
  }, [token, toast]);

  const toggleFavorite = useCallback(
    async (id) => {
      const exists = favorites.includes(id);
      if (token) {
        try {
          if (exists) {
            await removeFavoriteRs(id, token);
            setFavorites((current) => current.filter((item) => item !== id));
            toast('Rumah sakit dihapus dari daftar favorit akun.', 'info');
          } else {
            await addFavoriteRs(id, null, token);
            setFavorites((current) => [...new Set([...current, id])]);
            toast('Rumah sakit disimpan ke daftar favorit PostgreSQL.', 'success');
          }
          return;
        } catch (err) {
          toast(`Gagal memperbarui favorit: ${err.message}`, 'error');
          return;
        }
      }

      let added = false;
      setFavorites((current) => {
        if (current.includes(id)) return current.filter((item) => item !== id);
        added = true;
        return [...current, id];
      });
      toast(
        added
          ? 'Disimpan sementara di peramban. Masuk akun pasien untuk sinkronisasi permanen.'
          : 'Rumah sakit dihapus dari favorit.',
        added ? 'success' : 'info',
      );
    },
    [favorites, token, toast],
  );

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      login,
      registerAndLogin,
      logout,
      loginOpen,
      openLogin,
      closeLogin,
      toasts,
      toast,
      favorites,
      toggleFavorite,
      isFavorite: (id) => favorites.includes(id),
    }),
    [
      user,
      token,
      login,
      registerAndLogin,
      logout,
      loginOpen,
      openLogin,
      closeLogin,
      toasts,
      toast,
      favorites,
      toggleFavorite,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used inside AppProvider');
  return context;
}
