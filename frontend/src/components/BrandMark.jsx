import { Link } from 'react-router-dom';
export function BrandMark({dark=false,compact=false}) {
  return <Link to="/" aria-label="Cari Sehat, beranda" className={dark?'rounded-xl bg-white p-1':'inline-flex'}>
    <img src="/images/cari-sehat-logo.png" alt="Cari Sehat" style={{width:compact?170:190,height:compact?57:64,objectFit:'contain',maxWidth:'36vw'}} />
  </Link>;
}
