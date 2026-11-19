import sys
sys.path.insert(0, 'C:/K7/backend')
from app.services.fuzzy_search import normalize, expand, skor, skor_rs, rank, ALIAS_RS

mock_hospitals = [
    {'id': 'rs-171', 'nama': 'RS Umum Pusat H. Adam Malik', 'alamat': 'Jl. Bunga Lau No.17'},
    {'id': 'rs-083', 'nama': 'RS Umum Daerah Dr. Pirngadi', 'alamat': 'Jl. Prof HM Yamin'},
    {'id': 'rs-185', 'nama': 'RS Umum Siloam Dhirga Surya', 'alamat': 'Jl. Imam Bonjol'},
    {'id': 'rs-125', 'nama': 'RS Umum Hermina Medan', 'alamat': 'Jl. Asrama'},
    {'id': 'rs-142', 'nama': 'RS Umum Martha Friska', 'alamat': 'Jl. Yos Sudarso'},
    {'id': 'rs-143', 'nama': 'RS Umum Martha Friska Multatuli', 'alamat': 'Jl. Multatuli'},
    {'id': 'rs-037', 'nama': 'RS Metta Medika', 'alamat': 'Gunungsitoli'},
    {'id': 'rs-039', 'nama': 'RS Metta Medika II', 'alamat': 'Sibolga'},
]

test_queries = [
    'adam malik', 'rs adam malek', 'rsup ham', 'pringadi', 'siloan',
    'hermina', 'martha friska', 'rs metta medika', 'rs xyzabc'
]

for q in test_queries:
    scores = [(h['id'], h['nama'], skor_rs(q, h)) for h in mock_hospitals]
    scores.sort(key=lambda x: -x[2])
    top = scores[:2]
    print(f'Query "{q}": top 1: {top[0][1]} ({top[0][2]:.2f}), top 2: {top[1][1]} ({top[1][2]:.2f})')
