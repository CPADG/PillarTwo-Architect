#!/usr/bin/env python3
"""
Programmatic SEO 빌드 스크립트 — jurisdictions/{slug}.html 자동 생성.

데이터 구조 (각 국가):
  cc, slug, name_ko, name_en, name_ja, flag_cc
  iir   = {date, qualified, domestic_name(optional)}
  utpr  = {date, qualified}  # None이면 미도입
  qdmtt = {date, qualified, domestic_name(optional)}
  sbs   = {date, qualified}  # 선택적, US 등
  domestic_laws = [{name, detail}]
  recent_legislation = [{date, event}]
  sources = [{name, detail, url(optional)}]
  lead_extra = 자유 텍스트 (lead paragraph 보강)
  insights = [paragraph1, paragraph2, ...]

Korea iteration 규칙 엄밀 적용:
- PwC 출처 미수록
- 시행령/시행규칙 미수록 (법률 수준만)
- 시행 타임라인 — OECD 약어 일관 (IIR/UTPR/QDMTT)
- Quick reference — IIR=인정 / UTPR=평가 중 / QDMTT=케이스별 / SH=검토 필요
- '기업'·'아키텍처'·'분석해 보기'·'청사진'·'모기업 등의 소재지국'
"""

import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'jurisdictions'


# ─────────────────────────────────────────────────────────────────
# 국가 데이터
# ─────────────────────────────────────────────────────────────────

COUNTRIES = {
    # 수동 작성 페이지 (Batch 1) — 인덱스 카드 데이터만 보관. index_only=True 시 render_page 스킵
    'KR': {
        'slug': 'korea', 'name_ko': '대한민국', 'name_en': 'Korea', 'name_ja': '韓国', 'flag_cc': 'kr',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2026-01-01', 'qualified': False},
        'index_only': True,
        'skip_intl': True,
    },
    'JP': {
        'slug': 'japan', 'name_ko': '일본', 'name_en': 'Japan', 'name_ja': '日本', 'flag_cc': 'jp',
        'iir':   {'date': '2024-04-01', 'qualified': True},
        'utpr':  {'date': '2026-04-01', 'qualified': False},
        'qdmtt': {'date': '2026-04-01', 'qualified': True},
        'index_only': True,
        'skip_intl': True,
    },
    'US': {
        'slug': 'united-states', 'name_ko': '미국', 'name_en': 'United States', 'name_ja': 'アメリカ', 'flag_cc': 'us',
        'iir':   {'date': None, 'qualified': False, 'note': '미도입'},
        'utpr':  {'date': None, 'qualified': False, 'note': '미도입'},
        'qdmtt': {'date': None, 'qualified': False, 'note': '미도입'},
        'index_only': True,
        'skip_intl': True,
    },
    'GB': {
        'slug': 'united-kingdom', 'name_ko': '영국', 'name_en': 'United Kingdom', 'name_ja': 'イギリス', 'flag_cc': 'gb',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'index_only': True,
        'skip_intl': True,
    },

    'DE': {
        'slug': 'germany',
        'name_ko': '독일',
        'name_en': 'Germany',
        'name_ja': 'ドイツ',
        'flag_cc': 'de',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '독일은 <strong>Mindeststeuergesetz (MinStG)</strong>로 EU Directive 2022/2523을 자국 '
            '법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 '
            '시행되고 있으며, 시행일은 사업연도 개시일 기준입니다.'
        ),
        'domestic_laws': [
            ('<strong>Mindeststeuergesetz (MinStG)</strong>', '글로벌최저한세 IIR·QDMTT 일괄 도입 — EU Directive 2022/2523 transposition'),
            ('정식 명칭', 'Gesetz zur Gewährleistung einer globalen Mindestbesteuerung für Unternehmensgruppen'),
            ('UTPR', 'MinStG 후속 개정으로 2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('독일에 모기업', '독일에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다. 자회사 소재지국의 ETR이 15% 미만인 경우, 모기업 등의 소재지국(독일)에서 IIR에 따른 추가세액을 신고·납부해야 합니다.'),
            ('독일에 자회사', '독일에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 독일 QDMTT 적용 대상입니다. 독일 QDMTT는 OECD Central Record에 적격으로 등재되어 있어, QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024 ~ 현재', '후속 시행 가이드 및 EU·OECD 행정지침 반영 개정'),
            ('2023-12', 'Mindeststeuergesetz (MinStG) 공포 — 2023-12-31 이후 개시 사업연도부터 IIR·QDMTT 시행'),
        ],
        'sources': [
            ('Bundesministerium der Finanzen (독일 연방재무부)', 'Pillar Two 관련 정책 발표', 'https://www.bundesfinanzministerium.de/'),
            ('gesetze-im-internet.de', '독일 연방 법령 — Mindeststeuergesetz', 'https://www.gesetze-im-internet.de/'),
        ],
        'oecd_qualified_extras': 'gesetze-im-internet.de 안내 확인 권장',
    },

    'FR': {
        'slug': 'france',
        'name_ko': '프랑스',
        'name_en': 'France',
        'name_ja': 'フランス',
        'flag_cc': 'fr',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '프랑스는 <strong>Code général des impôts (CGI)</strong> Chapitre II bis (article 223 VJ '
            'à 223 WZ)으로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 '
            '2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Code général des impôts</strong>', 'Chapitre II bis, article 223 VJ à 223 WZ'),
            ('정식 명칭', "Imposition minimale mondiale des groupes d'entreprises multinationales et des groupes nationaux"),
            ('UTPR', 'CGI 개정으로 2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('프랑스에 모기업', '프랑스에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다. 모기업 등의 소재지국(프랑스)에서 자회사 소재지국의 저율과세 추가세액을 신고·납부합니다.'),
            ('프랑스에 자회사', '프랑스에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 프랑스 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024 ~ 현재', '후속 시행 가이드 및 OECD 행정지침 반영 개정'),
            ('2023', 'CGI 개정 — Chapitre II bis 신설로 2023-12-31 이후 개시 사업연도부터 IIR·QDMTT 시행'),
        ],
        'sources': [
            ('Direction générale des Finances publiques (DGFiP, 프랑스 국세청)', 'Pillar Two 안내', 'https://www.impots.gouv.fr/'),
            ('Légifrance', '프랑스 공식 법령 데이터베이스 — Code général des impôts', 'https://www.legifrance.gouv.fr/'),
        ],
    },

    'IT': {
        'slug': 'italy',
        'name_ko': '이탈리아',
        'name_en': 'Italy',
        'name_ja': 'イタリア',
        'flag_cc': 'it',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '이탈리아는 <strong>Decreto Legislativo 27 dicembre 2023, n. 209</strong>로 EU Directive '
            '2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 '
            '개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Decreto Legislativo 27 dicembre 2023, n. 209</strong>', "Attuazione della riforma fiscale in materia di fiscalita' internazionale"),
            ('IIR·QDMTT 시행', '2023-12-31 이후 개시 사업연도부터'),
            ('UTPR', '동 법령 후속 개정으로 2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('이탈리아에 모기업', '이탈리아에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다. 모기업 등의 소재지국(이탈리아)에서 자회사 소재지국의 저율과세 추가세액을 회수합니다.'),
            ('이탈리아에 자회사', '이탈리아에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 이탈리아 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024 ~ 현재', '후속 시행 가이드 및 OECD 행정지침 반영 개정'),
            ('2023-12-27', 'Decreto Legislativo n. 209 공포 — IIR·QDMTT 시행'),
        ],
        'sources': [
            ('Agenzia delle Entrate (이탈리아 국세청)', 'Pillar Two 안내', 'https://www.agenziaentrate.gov.it/'),
            ('Normattiva', '이탈리아 공식 법령 데이터베이스', 'https://www.normattiva.it/'),
        ],
    },

    'NL': {
        'slug': 'netherlands',
        'name_ko': '네덜란드',
        'name_en': 'Netherlands',
        'name_ja': 'オランダ',
        'flag_cc': 'nl',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '네덜란드는 <strong>Wet minimumbelasting 2024</strong>로 EU Directive 2022/2523을 자국 '
            '법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 '
            '시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Wet minimumbelasting 2024</strong>', '글로벌최저한세 IIR·QDMTT 일괄 도입 — EU Directive 2022/2523 transposition'),
            ('IIR·QDMTT 시행', '2023-12-31 이후 개시 사업연도부터'),
            ('UTPR', '동 법령 개정으로 2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('네덜란드에 모기업', '네덜란드에 모기업(특히 지주회사)을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다. 네덜란드는 글로벌 지주회사 hub 역할이 큰 만큼 IIR 적용 빈도가 높습니다.'),
            ('네덜란드에 자회사', '네덜란드에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 네덜란드 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024 ~ 현재', '후속 시행 가이드 및 OECD 행정지침 반영 개정'),
            ('2023', 'Wet minimumbelasting 2024 공포 — IIR·QDMTT 시행'),
        ],
        'sources': [
            ('Belastingdienst (네덜란드 국세청)', 'Pillar Two 안내', 'https://www.belastingdienst.nl/'),
            ('Overheid.nl', '네덜란드 공식 법령 데이터베이스 — Wet minimumbelasting 2024', 'https://wetten.overheid.nl/'),
        ],
    },

    'AU': {
        'slug': 'australia',
        'name_ko': '호주',
        'name_en': 'Australia',
        'name_ja': 'オーストラリア',
        'flag_cc': 'au',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': (
            '호주는 <strong>Taxation (Multinational – Global and Domestic Minimum Tax) Act 2024</strong> '
            '및 동 Imposition Act로 OECD Pillar Two를 도입했습니다. IIR과 QDMTT는 2024-01-01, UTPR은 '
            '1년 지연되어 2025-01-01 이후 개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Taxation (Multinational – Global and Domestic Minimum Tax) Act 2024 (Assessment Act)</strong>', 'IIR·UTPR·QDMTT 본 규정'),
            ('<strong>Taxation (Multinational – Global and Domestic Minimum Tax) Imposition Act 2024</strong>', '추가세액 부과 근거'),
            ('<strong>Treasury Laws Amendment (Multinational – Global and Domestic Minimum Tax) Act 2024</strong>', '관련 법률 개정 (시행 및 기술적 사항)'),
            ('UTPR', '1년 지연되어 2025-01-01 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('호주에 모기업', '호주에 모기업을 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR 의무를 부담합니다. 자회사 소재지국의 ETR이 15% 미만인 경우, 모기업 등의 소재지국(호주)에서 IIR에 따른 추가세액을 신고·납부해야 합니다.'),
            ('호주에 자회사', '호주에 자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 호주 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
            ('회계연도 7월 개시 관행', '호주 기업의 표준 회계연도는 7월 1일 개시가 일반적입니다. 1월·4월 개시 회계연도를 사용하는 다른 국가의 모기업·자회사와 그룹 단위로 분석할 때 적용 회계연도 매핑에 주의가 필요합니다.'),
        ],
        'recent': [
            ('2024-12', 'Pillar Two 본 법률 일괄 통과 — Assessment Act + Imposition Act + 관련 개정 (2024-01-01 소급 시행)'),
        ],
        'sources': [
            ('Australian Taxation Office (ATO)', 'Pillar Two 안내 및 가이드', 'https://www.ato.gov.au/'),
            ('Federal Register of Legislation', '호주 연방 법령 — Taxation (Multinational – Global and Domestic Minimum Tax) Act 2024', 'https://www.legislation.gov.au/'),
        ],
    },

    'HK': {
        'slug': 'hong-kong',
        'name_ko': '홍콩',
        'name_en': 'Hong Kong (China)',
        'name_ja': '香港',
        'flag_cc': 'hk',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True, 'domestic_name': 'Hong Kong Minimum Top-up Tax (HKMTT)'},
        'lead': (
            '홍콩은 <strong>Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) '
            'Ordinance 2025</strong>로 OECD Pillar Two를 도입했습니다. IIR과 QDMTT(국내 도입명: Hong Kong '
            'Minimum Top-up Tax, HKMTT)는 2025-01-01 이후 개시 사업연도부터 시행되며, UTPR은 아직 별도로 '
            '발표되지 않은 상태입니다.'
        ),
        'domestic_laws': [
            ('<strong>Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025</strong>', '2025-06-06 제정. IIR + HKMTT(QDMTT 상당) 일괄 도입'),
            ('UTPR', '도입 미발표'),
        ],
        'insights': [
            ('홍콩에 모기업', '홍콩에 모기업을 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('홍콩에 자회사', '홍콩에 자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 HKMTT(QDMTT) 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. 홍콩의 표준 법인세율(16.5%)과 영역원천주의(territorial taxation) 영향으로 자회사 ETR이 15% 미만이 되는 경우가 적지 않으므로 사전 모델링 가치가 큽니다.'),
            ('APAC 금융 hub 특성', '홍콩은 APAC 지역의 금융·홀딩 기능이 집중된 소재지국으로, Pillar Two 분석 시 홍콩 영역원천주의 세제와의 상호작용을 별도로 검토할 필요가 있습니다.'),
        ],
        'recent': [
            ('2025-06-06', 'Inland Revenue (Amendment) Ordinance 2025 제정 — IIR + HKMTT 일괄 도입 (2025-01-01 시행)'),
        ],
        'sources': [
            ('Inland Revenue Department (IRD)', 'Pillar Two 안내', 'https://www.ird.gov.hk/'),
            ('Hong Kong e-Legislation', '홍콩 법령 데이터베이스 — Inland Revenue (Amendment) Ordinance 2025', 'https://www.elegislation.gov.hk/'),
        ],
    },

    'IE': {
        'slug': 'ireland',
        'name_ko': '아일랜드',
        'name_en': 'Ireland',
        'name_ja': 'アイルランド',
        'flag_cc': 'ie',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True, 'domestic_name': 'Qualified Domestic Top-up Tax (QDTT)'},
        'lead': (
            '아일랜드는 <strong>Taxes Consolidation Act 1997 Part 4A</strong>로 EU Directive 2022/2523을 '
            '자국 법령으로 도입했습니다. IIR과 QDMTT(국내 도입명: Qualified Domestic Top-up Tax, QDTT)는 '
            '2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Taxes Consolidation Act 1997, Part 4A</strong>', 'EU Directive 2022/2523 transposition. 2023-12-18 제정'),
            ('IIR · QDTT(QDMTT)', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('아일랜드에 모기업', '아일랜드에 모기업(특히 글로벌 IT·제약 그룹의 EMEA 본부)을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('아일랜드에 자회사', '아일랜드에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 아일랜드 QDTT(QDMTT) 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. 아일랜드 표준 법인세율(12.5%)이 글로벌최저한세율(15%) 미만이므로 자회사 ETR이 임계치 하회하는 사례가 많아 사전 모델링이 특히 중요합니다.'),
            ('Tech·Pharma 헤드쿼터 hub 특성', '아일랜드는 글로벌 IT·제약 기업의 본부·IP 보유 기능이 집중된 소재지국입니다. Pillar Two 분석 시 아일랜드의 R&D 세액공제, IP regime 등과의 상호작용을 별도로 검토할 필요가 있습니다.'),
        ],
        'recent': [
            ('2023-12-18', 'Taxes Consolidation Act 1997 Part 4A 제정 — IIR · QDTT 시행'),
        ],
        'sources': [
            ('Revenue Commissioners', '아일랜드 국세청 Pillar Two 안내', 'https://www.revenue.ie/'),
            ('Irish Statute Book', '아일랜드 법령 데이터베이스 — Taxes Consolidation Act 1997', 'https://www.irishstatutebook.ie/'),
        ],
    },

    'LU': {
        'slug': 'luxembourg',
        'name_ko': '룩셈부르크',
        'name_en': 'Luxembourg',
        'name_ja': 'ルクセンブルク',
        'flag_cc': 'lu',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '룩셈부르크는 <strong>Loi du 22 décembre 2023</strong>로 EU Directive 2022/2523을 자국 '
            '법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 '
            '시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Loi du 22 décembre 2023</strong>', "Relative à l'imposition minimale effective en vue de la transposition de la directive (UE) 2022/2523. 2023-12-20 채택"),
            ('IIR · QDMTT', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('룩셈부르크에 모기업', '룩셈부르크에 모기업(특히 EU 지주회사 hub로 활용되는 SOPARFI 등)을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('룩셈부르크에 자회사', '룩셈부르크에 자회사·금융 vehicle을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 룩셈부르크 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
            ('EU 지주회사 hub 특성', '룩셈부르크는 EU 지주회사·투자펀드·증권화 vehicle 등의 hub로 활용되는 소재지국입니다. Pillar Two 분석 시 SOPARFI·SICAR·SICAV 등 vehicle 유형별 적용 가능성과 함께 룩셈부르크의 IP regime 등과의 상호작용을 별도로 검토할 필요가 있습니다.'),
        ],
        'recent': [
            ('2023-12-22', 'Loi du 22 décembre 2023 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Administration des contributions directes (ACD)', '룩셈부르크 직접세청 Pillar Two 안내', 'https://impotsdirects.public.lu/'),
            ('Legilux', '룩셈부르크 공식 법령 데이터베이스', 'https://legilux.public.lu/'),
        ],
    },

    'BE': {
        'slug': 'belgium',
        'name_ko': '벨기에',
        'name_en': 'Belgium',
        'name_ja': 'ベルギー',
        'flag_cc': 'be',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            "벨기에는 2023-12-14 가결된 <strong>Loi du 19 décembre 2023 / Wet van 19 december 2023</strong> "
            "(다국적기업그룹·대규모 국내그룹에 대한 최저세 도입 법률)로 EU Directive 2022/2523을 자국 법령으로 "
            "도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행되고 있습니다."
        ),
        'domestic_laws': [
            ("<strong>Loi du 19 décembre 2023 / Wet van 19 december 2023</strong>", "다국적기업그룹 및 대규모 국내그룹에 대한 최저세 도입 — EU Directive 2022/2523 transposition. 2023-12-14 가결, Belgisch Staatsblad 공포"),
            ('IIR · QDMTT', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('벨기에에 모기업', '벨기에에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('벨기에에 자회사', '벨기에에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 벨기에 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2023-12-14', '벨기에 의회 가결, Belgisch Staatsblad 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Service Public Fédéral Finances (SPF Finances, 벨기에 연방재무부)', 'Pillar Two 안내', 'https://finance.belgium.be/'),
            ('Belgisch Staatsblad / Moniteur belge', '벨기에 공식 관보', 'https://www.ejustice.just.fgov.be/'),
        ],
    },

    'CA': {
        'slug': 'canada',
        'name_ko': '캐나다',
        'name_en': 'Canada',
        'name_ja': 'カナダ',
        'flag_cc': 'ca',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2025-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '캐나다는 <strong>Global Minimum Tax Act</strong>(Loi sur l\'impôt minimum mondial)로 OECD '
            'Pillar Two를 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2년 지연되어 2025-12-31 이후 '
            '개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Global Minimum Tax Act / Loi sur l\'impôt minimum mondial</strong>', '연방 법령 — 영어·프랑스어 동시 공포'),
            ('IIR · QDMTT', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2년 지연되어 2025-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('캐나다에 모기업', '캐나다에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('캐나다에 자회사', '캐나다에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 캐나다 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024', 'Global Minimum Tax Act 시행 — IIR · QDMTT 적용'),
        ],
        'sources': [
            ('Canada Revenue Agency (CRA)', '캐나다 국세청 Pillar Two 안내', 'https://www.canada.ca/en/revenue-agency.html'),
            ('Justice Laws Website', '캐나다 연방 법령 데이터베이스', 'https://laws-lois.justice.gc.ca/'),
        ],
    },

    'BR': {
        'slug': 'brazil',
        'name_ko': '브라질',
        'name_en': 'Brazil',
        'name_ja': 'ブラジル',
        'flag_cc': 'br',
        'iir':   {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': (
            '브라질은 <strong>Lei n.º 15.079, de 27 de dezembro de 2024</strong>로 OECD Pillar Two의 '
            'QDMTT를 우선 도입했습니다. QDMTT는 2025-01-01 이후 개시 사업연도부터 시행되며, IIR과 '
            'UTPR은 아직 별도로 발표되지 않은 상태입니다.'
        ),
        'domestic_laws': [
            ('<strong>Lei n.º 15.079, de 27 de dezembro de 2024</strong>', 'QDMTT 도입 법률 — 2024-12-27 공포'),
            ('IIR · UTPR', '도입 미발표'),
        ],
        'insights': [
            ('브라질에 자회사', '브라질에 자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 브라질 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
            ('IIR·UTPR 미도입', '브라질은 IIR과 UTPR을 별도로 도입하지 않은 상태로, 현재 시행 중인 Pillar Two 관련 규정은 QDMTT뿐입니다. 향후 입법 동향에 대한 모니터링이 필요합니다.'),
        ],
        'recent': [
            ('2024-12-27', 'Lei n.º 15.079 공포 — QDMTT 도입 (2025-01-01 시행)'),
        ],
        'sources': [
            ('Receita Federal do Brasil (RFB)', '브라질 연방국세청 Pillar Two 안내', 'https://www.gov.br/receitafederal/'),
            ('Planalto', '브라질 공식 법령 데이터베이스', 'https://www.planalto.gov.br/'),
        ],
    },

    'AE': {
        'slug': 'united-arab-emirates',
        'name_ko': '아랍에미리트',
        'name_en': 'United Arab Emirates',
        'name_ja': 'アラブ首長国連邦',
        'flag_cc': 'ae',
        'iir':   {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': (
            '아랍에미리트는 <strong>Cabinet Decision No. 142 of 2024</strong>(다국적기업그룹에 대한 '
            '추가세 부과)로 OECD Pillar Two의 QDMTT를 도입했습니다. QDMTT는 2025-01-01 이후 개시 '
            '사업연도부터 시행되며, IIR과 UTPR은 아직 별도로 발표되지 않은 상태입니다.'
        ),
        'domestic_laws': [
            ('<strong>Cabinet Decision No. 142 of 2024</strong>', 'On the Imposition of Top-up Tax on Multinational Enterprises — QDMTT 도입'),
            ('IIR · UTPR', '도입 미발표'),
        ],
        'insights': [
            ('UAE에 자회사', 'UAE에 자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 UAE QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. UAE 표준 법인세율(9%)이 글로벌최저한세율(15%) 미만이므로 자회사 ETR이 임계치 하회하는 사례가 많아 사전 모델링이 특히 중요합니다.'),
            ('중동 hub 특성', 'UAE는 중동 지역의 본부·금융·물류 hub로 활용되며 Free Zone(자유무역지대) 인센티브가 광범위하게 적용됩니다. Pillar Two 분석 시 Free Zone qualifying entity 여부, Free Zone 인센티브와의 상호작용을 별도로 검토할 필요가 있습니다.'),
        ],
        'recent': [
            ('2024', 'Cabinet Decision No. 142 of 2024 공포 — QDMTT 도입 (2025-01-01 시행)'),
        ],
        'sources': [
            ('Federal Tax Authority (FTA)', 'UAE 연방세무청 Pillar Two 안내', 'https://tax.gov.ae/'),
            ('UAE Ministry of Finance', '재무부 발표', 'https://mof.gov.ae/'),
        ],
    },

    'SE': {
        'slug': 'sweden',
        'name_ko': '스웨덴',
        'name_en': 'Sweden',
        'name_ja': 'スウェーデン',
        'flag_cc': 'se',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '스웨덴은 <strong>Lag (2023:875) om tilläggsskatt</strong>(추가세에 관한 법률)로 EU '
            'Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 '
            '2024-12-31 이후 개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Lag (2023:875) om tilläggsskatt</strong>', '추가세에 관한 법률 — EU Directive 2022/2523 transposition'),
            ('IIR · QDMTT', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('스웨덴에 모기업', '스웨덴에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('스웨덴에 자회사', '스웨덴에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 스웨덴 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2023', 'Lag (2023:875) om tilläggsskatt 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Skatteverket (스웨덴 국세청)', 'Pillar Two 안내', 'https://www.skatteverket.se/'),
            ('Riksdagen', '스웨덴 공식 법령 데이터베이스', 'https://www.riksdagen.se/'),
        ],
    },

    'ES': {
        'slug': 'spain',
        'name_ko': '스페인',
        'name_en': 'Spain',
        'name_ja': 'スペイン',
        'flag_cc': 'es',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': (
            '스페인은 <strong>Ley 7/2024, de 20 de diciembre</strong>(다국적기업그룹·대규모 국내그룹의 '
            '글로벌최저한세 보충세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. '
            'IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행되고 있습니다.'
        ),
        'domestic_laws': [
            ('<strong>Ley 7/2024, de 20 de diciembre</strong>', '다국적기업그룹·대규모 국내그룹 대상 보충세 도입 — EU Directive 2022/2523 transposition'),
            ('IIR · QDMTT', '2023-12-31 이후 개시 사업연도부터 시행'),
            ('UTPR', '2024-12-31 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('스페인에 모기업', '스페인에 모기업을 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('스페인에 자회사', '스페인에 자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 스페인 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024-12-20', 'Ley 7/2024 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Agencia Tributaria (AEAT, 스페인 국세청)', 'Pillar Two 안내', 'https://sede.agenciatributaria.gob.es/'),
            ('Boletín Oficial del Estado (BOE)', '스페인 공식 관보', 'https://www.boe.es/'),
        ],
    },

    'CH': {
        'slug': 'switzerland',
        'name_ko': '스위스',
        'name_en': 'Switzerland',
        'name_ja': 'スイス',
        'flag_cc': 'ch',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': (
            '스위스는 <strong>Ordonnance sur l\'imposition minimale des grands groupes d\'entreprises '
            '(RS 642.161)</strong>로 OECD Pillar Two를 도입했습니다. QDMTT는 2024-01-01부터 우선 시행되었고, '
            'IIR은 2025-01-01 이후 개시 사업연도부터 시행됩니다. UTPR은 아직 별도로 발표되지 않은 상태입니다.'
        ),
        'domestic_laws': [
            ('<strong>Ordonnance sur l\'imposition minimale des grands groupes d\'entreprises (RS 642.161)</strong>', '2023-12-22 채택. 프랑스어·독일어·이탈리아어 동시 공포'),
            ('QDMTT', '2024-01-01 시행 (선행 도입)'),
            ('IIR', '2025-01-01 이후 개시 사업연도부터 시행'),
            ('UTPR', '도입 미발표'),
        ],
        'insights': [
            ('스위스에 모기업', '스위스에 모기업을 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('스위스에 자회사', '스위스에 자회사를 둔 다국적기업그룹은 이미 2024-01-01 이후 개시 사업연도부터 스위스 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
            ('QDMTT 선행 도입', '스위스는 QDMTT를 IIR보다 1년 앞서 도입했습니다. 자국 세수 확보를 우선 위한 입법 순서로, 그룹 분석 시 동일 사업연도에 두 규정이 서로 다른 시점에 적용되는 점을 유의할 필요가 있습니다.'),
            ('헤드쿼터·금융 hub 특성', '스위스는 글로벌 본부·금융·연구 기능이 집중된 소재지국으로, 칸톤(주)별로 차등화된 법인세율과 특별 인센티브 영향으로 자회사 ETR이 임계치 하회하는 사례가 발생할 수 있습니다.'),
        ],
        'recent': [
            ('2023-12-22', 'RS 642.161 채택 — QDMTT 우선 시행 (2024-01-01)'),
            ('2024', 'IIR 시행 시점 확정 (2025-01-01)'),
        ],
        'sources': [
            ('Eidgenössische Steuerverwaltung (ESTV, 스위스 연방세무청)', 'Pillar Two 안내', 'https://www.estv.admin.ch/'),
            ('Fedlex', '스위스 공식 법령 데이터베이스 — RS 642.161', 'https://www.fedlex.admin.ch/'),
        ],
    },

    'SG': {
        'slug': 'singapore',
        'name_ko': '싱가포르',
        'name_en': 'Singapore',
        'name_ja': 'シンガポール',
        'flag_cc': 'sg',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': (
            '싱가포르는 <strong>Multinational Enterprise (Minimum Tax) Act 2024</strong>로 OECD Pillar '
            'Two의 IIR과 QDMTT를 도입했습니다. 두 규정 모두 2025-01-01 이후 개시 사업연도부터 시행되며, '
            'UTPR은 아직 별도로 발표되지 않은 상태입니다.'
        ),
        'domestic_laws': [
            ('<strong>Multinational Enterprise (Minimum Tax) Act 2024</strong>', 'IIR + QDMTT 일괄 도입 — 2025-01-01 시행'),
            ('UTPR', '도입 미발표'),
        ],
        'insights': [
            ('싱가포르에 모기업', '싱가포르에 모기업(특히 APAC 지역본부)을 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR 의무를 부담합니다.'),
            ('싱가포르에 자회사', '싱가포르에 자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 싱가포르 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. 싱가포르의 표준 법인세율(17%)과 다양한 인센티브 영향으로 자회사 ETR이 15% 미만이 되는 경우가 적지 않으므로 사전 모델링 가치가 높습니다.'),
            ('APAC hub 특성', '싱가포르는 APAC 지역 본부·재무·홀딩 기능이 집중된 국가로, 다국적기업그룹 분석 시 싱가포르의 인센티브 세제(예: Pioneer Status, Development & Expansion Incentive 등)와 Pillar Two의 상호작용을 별도로 검토할 필요가 있습니다.'),
        ],
        'recent': [
            ('2024', 'Multinational Enterprise (Minimum Tax) Act 2024 공포 — IIR·QDMTT 시행 (2025-01-01)'),
        ],
        'sources': [
            ('Inland Revenue Authority of Singapore (IRAS, 싱가포르 국세청)', 'Pillar Two 안내', 'https://www.iras.gov.sg/'),
            ('Singapore Statutes Online', '싱가포르 공식 법령 데이터베이스', 'https://sso.agc.gov.sg/'),
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # Batch 4 — 차순위 20국 (slightly simpler narrative)
    # ─────────────────────────────────────────────────────────────────

    'VN': {
        'slug': 'vietnam', 'name_ko': '베트남', 'name_en': 'Vietnam', 'name_ja': 'ベトナム', 'flag_cc': 'vn',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '베트남은 <strong>Nghị quyết số 107/2023/QH15</strong>(추가법인소득세 적용에 관한 국회결의)로 OECD Pillar Two의 IIR과 QDMTT를 도입했습니다. 시행일은 2024-01-01 이후 개시 사업연도입니다.',
        'domestic_laws': [
            ('<strong>Nghị quyết số 107/2023/QH15</strong>', 'Quốc hội (베트남 국회) 결의 — IIR + QDMTT 도입. 2023-11-29 채택, 2024-01-01 시행'),
        ],
        'insights': [
            ('베트남에 모기업·자회사', '베트남에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 베트남 IIR과 QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. 베트남 표준 법인세율(20%) 외에 다양한 세제 인센티브(첨단기술기업·경제구역 등) 영향으로 자회사 ETR이 임계치 하회하는 사례가 있어 사전 모델링 가치가 있습니다.'),
        ],
        'recent': [
            ('2023-11-29', 'Nghị quyết số 107/2023/QH15 채택 — IIR · QDMTT 시행 (2024-01-01)'),
        ],
        'sources': [
            ('Tổng cục Thuế (General Department of Taxation)', '베트남 국세청', 'https://www.gdt.gov.vn/'),
            ('Bộ Tài chính', '베트남 재무부', 'https://www.mof.gov.vn/'),
        ],
    },

    'ID': {
        'slug': 'indonesia', 'name_ko': '인도네시아', 'name_en': 'Indonesia', 'name_ja': 'インドネシア', 'flag_cc': 'id',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': '2026-01-01', 'qualified': False},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': '인도네시아는 <strong>PMK 136 TAHUN 2024</strong>(국제 합의에 따른 글로벌 최저법인세 부과)로 OECD Pillar Two를 도입했습니다. IIR과 QDMTT는 2025-01-01, UTPR은 2026-01-01 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Peraturan Menteri Keuangan (PMK) 136 TAHUN 2024</strong>', '재무부령 — IIR + QDMTT 일괄 도입'),
            ('UTPR', '2026-01-01 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('인도네시아에 모기업·자회사', '인도네시아에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2024', 'PMK 136 TAHUN 2024 공포 — IIR · QDMTT 시행 (2025-01-01)'),
        ],
        'sources': [
            ('Direktorat Jenderal Pajak (DJP)', '인도네시아 국세청', 'https://www.pajak.go.id/'),
            ('Kementerian Keuangan', '인도네시아 재무부', 'https://www.kemenkeu.go.id/'),
        ],
    },

    'MY': {
        'slug': 'malaysia', 'name_ko': '말레이시아', 'name_en': 'Malaysia', 'name_ja': 'マレーシア', 'flag_cc': 'my',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': '말레이시아는 <strong>Act 851 — Finance (No. 2) Act 2023, Section 30</strong>으로 OECD Pillar Two의 IIR과 QDMTT를 도입했습니다. 시행일은 2025-01-01 이후 개시 사업연도이며, UTPR은 아직 별도로 발표되지 않은 상태입니다.',
        'domestic_laws': [
            ('<strong>Act 851 — Finance (No. 2) Act 2023, Section 30</strong>', 'IIR + QDMTT 도입'),
        ],
        'insights': [
            ('말레이시아에 모기업·자회사', '말레이시아에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2023', 'Finance (No. 2) Act 2023 공포 — IIR · QDMTT 시행 (2025-01-01)'),
        ],
        'sources': [
            ('Inland Revenue Board of Malaysia (LHDN)', '말레이시아 국세청', 'https://www.hasil.gov.my/'),
            ('Ministry of Finance Malaysia', '말레이시아 재무부', 'https://www.mof.gov.my/'),
        ],
    },

    'TH': {
        'slug': 'thailand', 'name_ko': '태국', 'name_en': 'Thailand', 'name_ja': 'タイ', 'flag_cc': 'th',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': '태국은 <strong>พระราชกำหนดภาษีส่วนเพิ่ม พ.ศ. 2567</strong>(추가세에 관한 비상법령)로 OECD Pillar Two를 도입했습니다. IIR · UTPR · QDMTT 모두 2025-01-01 이후 개시 사업연도부터 동시에 시행됩니다.',
        'domestic_laws': [
            ('<strong>พระราชกำหนดภาษีส่วนเพิ่ม พ.ศ. 2567 (Top-up Tax Emergency Decree B.E. 2567)</strong>', '비상법령으로 IIR · UTPR · QDMTT 일괄 도입'),
        ],
        'insights': [
            ('태국에 모기업·자회사', '태국에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR · UTPR · QDMTT 모두 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다. 태국 BOI(Board of Investment) 인센티브 영향으로 자회사 ETR이 임계치 하회하는 경우가 있어 사전 모델링 가치가 있습니다.'),
        ],
        'recent': [
            ('2024', 'พระราชกำหนดภาษีส่วนเพิ่ม 공포 — IIR · UTPR · QDMTT 동시 시행 (2025-01-01)'),
        ],
        'sources': [
            ('Revenue Department', '태국 국세청', 'https://www.rd.go.th/'),
            ('Ministry of Finance', '태국 재무부', 'https://www.mof.go.th/'),
        ],
    },

    'NZ': {
        'slug': 'new-zealand', 'name_ko': '뉴질랜드', 'name_en': 'New Zealand', 'name_ja': 'ニュージーランド', 'flag_cc': 'nz',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2026-01-01', 'qualified': False},
        'lead': '뉴질랜드는 <strong>Taxation (Annual Rates for 2023–24, Multinational Tax, and Remedial Matters) Act 2024</strong>로 OECD Pillar Two를 도입했습니다. IIR과 UTPR은 2025-01-01, QDMTT는 1년 늦은 2026-01-01 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Taxation (Annual Rates for 2023–24, Multinational Tax, and Remedial Matters) Act 2024</strong>', 'IIR · UTPR · QDMTT 도입'),
            ('QDMTT', '1년 늦은 2026-01-01 이후 개시 사업연도부터 시행'),
        ],
        'insights': [
            ('뉴질랜드에 모기업·자회사', '뉴질랜드에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR/UTPR 적용 대상이며, 2026-01-01부터는 QDMTT가 추가로 적용됩니다.'),
        ],
        'recent': [
            ('2024', 'Taxation Act 2024 공포 — IIR/UTPR 2025-01-01, QDMTT 2026-01-01 시행'),
        ],
        'sources': [
            ('Inland Revenue (IR)', '뉴질랜드 국세청', 'https://www.ird.govt.nz/'),
            ('New Zealand Legislation', '뉴질랜드 법령 데이터베이스', 'https://www.legislation.govt.nz/'),
        ],
    },

    'AT': {
        'slug': 'austria', 'name_ko': '오스트리아', 'name_en': 'Austria', 'name_ja': 'オーストリア', 'flag_cc': 'at',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '오스트리아는 <strong>Mindestbesteuerungsgesetz (MinBestG)</strong>로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Bundesgesetz zur Gewährleistung einer globalen Mindestbesteuerung für Unternehmensgruppen (Mindestbesteuerungsgesetz – MinBestG)</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('오스트리아에 모기업·자회사', '오스트리아에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. QDMTT Safe Harbour 적용 요건을 충족하면 모기업 등의 소재지국에서의 IIR/UTPR 계산이 면제될 수 있습니다.'),
        ],
        'recent': [
            ('2023', 'MinBestG 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Bundesministerium für Finanzen (BMF)', '오스트리아 연방재무부', 'https://www.bmf.gv.at/'),
            ('Rechtsinformationssystem (RIS)', '오스트리아 법령 정보 시스템', 'https://www.ris.bka.gv.at/'),
        ],
    },

    'PL': {
        'slug': 'poland', 'name_ko': '폴란드', 'name_en': 'Poland', 'name_ja': 'ポーランド', 'flag_cc': 'pl',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': '폴란드는 <strong>Ustawa z dnia 6 listopada 2024 r.</strong>(다국적기업그룹·국내그룹의 보충세 과세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR · UTPR · QDMTT 모두 2025-01-01 이후 개시 사업연도부터 동시에 시행됩니다.',
        'domestic_laws': [
            ('<strong>Ustawa z dnia 6 listopada 2024 r. (Dz.U. 2024 poz.1685)</strong>', 'EU Directive 2022/2523 transposition — IIR · UTPR · QDMTT 일괄 도입'),
        ],
        'insights': [
            ('폴란드에 모기업·자회사', '폴란드에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR · UTPR · QDMTT 모두 적용 대상입니다.'),
        ],
        'recent': [
            ('2024-11-06', '법률 채택 — IIR · UTPR · QDMTT 동시 시행 (2025-01-01)'),
        ],
        'sources': [
            ('Krajowa Administracja Skarbowa (KAS)', '폴란드 국세청', 'https://www.podatki.gov.pl/'),
            ('Internetowy System Aktów Prawnych (ISAP)', '폴란드 법령 데이터베이스', 'https://isap.sejm.gov.pl/'),
        ],
    },

    'HU': {
        'slug': 'hungary', 'name_ko': '헝가리', 'name_en': 'Hungary', 'name_ja': 'ハンガリー', 'flag_cc': 'hu',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '헝가리는 <strong>2023. évi LXXXIV. Törvény</strong>(글로벌 최저 과세 보장 보충세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>2023. évi LXXXIV. Törvény</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('헝가리에 모기업·자회사', '헝가리에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. 헝가리 표준 법인세율(9%)이 글로벌최저한세율(15%)보다 낮으므로 자회사 ETR이 임계치 하회하는 사례가 많아 사전 모델링이 중요합니다.'),
        ],
        'recent': [
            ('2023', '2023. évi LXXXIV. Törvény 채택 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Nemzeti Adó- és Vámhivatal (NAV)', '헝가리 국세청', 'https://nav.gov.hu/'),
            ('Magyar Közlöny', '헝가리 공식 관보', 'https://magyarkozlony.hu/'),
        ],
    },

    'CZ': {
        'slug': 'czech-republic', 'name_ko': '체코', 'name_en': 'Czechia', 'name_ja': 'チェコ', 'flag_cc': 'cz',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '체코는 <strong>Zákon č. 416/2023 Sb.</strong>(대규모 다국적그룹 및 국내그룹에 대한 보충세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Zákon č. 416/2023 Sb.</strong>', 'O dorovnávacích daních pro velké nadnárodní skupiny a velké vnitrostátní skupiny — EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('체코에 모기업·자회사', '체코에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023', 'Zákon č. 416/2023 Sb. 채택 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Finanční správa České republiky', '체코 국세청', 'https://www.financnisprava.cz/'),
            ('Zákony pro lidi', '체코 법령 데이터베이스', 'https://www.zakonyprolidi.cz/'),
        ],
    },

    'DK': {
        'slug': 'denmark', 'name_ko': '덴마크', 'name_en': 'Denmark', 'name_ja': 'デンマーク', 'flag_cc': 'dk',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '덴마크는 <strong>Minimumsbeskatningsloven (Lov nr. 1535 af 12. december 2023)</strong>로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Lov nr. 1535 af 12. december 2023 om en ekstraskat for visse koncernenheder (Minimumsbeskatningsloven)</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('덴마크에 모기업·자회사', '덴마크에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023-12-12', 'Lov nr. 1535 채택 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Skattestyrelsen', '덴마크 국세청', 'https://www.skat.dk/'),
            ('Retsinformation', '덴마크 법령 데이터베이스', 'https://www.retsinformation.dk/'),
        ],
    },

    'FI': {
        'slug': 'finland', 'name_ko': '핀란드', 'name_en': 'Finland', 'name_ja': 'フィンランド', 'flag_cc': 'fi',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '핀란드는 <strong>Laki suurten konsernien vähimmäisverosta (1308/2023)</strong>(대규모 그룹의 최저세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Laki suurten konsernien vähimmäisverosta 1308/2023</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('핀란드에 모기업·자회사', '핀란드에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023', 'Laki 1308/2023 채택 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Verohallinto', '핀란드 국세청', 'https://www.vero.fi/'),
            ('Finlex', '핀란드 법령 데이터베이스', 'https://www.finlex.fi/'),
        ],
    },

    'NO': {
        'slug': 'norway', 'name_ko': '노르웨이', 'name_en': 'Norway', 'name_ja': 'ノルウェー', 'flag_cc': 'no',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '노르웨이는 <strong>Suppleringsskatteloven (Lov 12. januar 2024 nr. 1)</strong>(보충세에 관한 법률)로 OECD Pillar Two를 도입했습니다. IIR과 QDMTT는 2024-01-01, UTPR은 2025-01-01 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Lov 12. januar 2024 nr. 1 om suppleringsskatt på underbeskattet inntekt i konsern (Suppleringsskatteloven)</strong>', 'EFTA 회원국 — OECD 모델규정 자체 도입'),
        ],
        'insights': [
            ('노르웨이에 모기업·자회사', '노르웨이에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2024-01-12', 'Suppleringsskatteloven 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Skatteetaten', '노르웨이 국세청', 'https://www.skatteetaten.no/'),
            ('Lovdata', '노르웨이 법령 데이터베이스', 'https://lovdata.no/'),
        ],
    },

    'PT': {
        'slug': 'portugal', 'name_ko': '포르투갈', 'name_en': 'Portugal', 'name_ja': 'ポルトガル', 'flag_cc': 'pt',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '포르투갈은 <strong>Lei n.º 41/2024, de 8 de novembro</strong>으로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2024-01-01, UTPR은 2025-01-01 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Lei n.º 41/2024, de 8 de novembro</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('포르투갈에 모기업·자회사', '포르투갈에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2024-11-08', 'Lei n.º 41/2024 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Autoridade Tributária e Aduaneira (AT)', '포르투갈 국세청', 'https://www.portaldasfinancas.gov.pt/'),
            ('Diário da República', '포르투갈 공식 관보', 'https://dre.pt/'),
        ],
    },

    'GR': {
        'slug': 'greece', 'name_ko': '그리스', 'name_en': 'Greece', 'name_ja': 'ギリシャ', 'flag_cc': 'gr',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '그리스는 <strong>Νόμος 5100/2024</strong>(EU 글로벌 최저과세 디렉티브 transposition)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Νόμος 5100/2024 (Law 5100/2024)</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('그리스에 모기업·자회사', '그리스에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2024', 'Νόμος 5100/2024 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Ανεξάρτητη Αρχή Δημοσίων Εσόδων (AADE)', '그리스 국세청', 'https://www.aade.gr/'),
            ('Εθνικό Τυπογραφείο', '그리스 공식 관보', 'https://www.et.gr/'),
        ],
    },

    'RO': {
        'slug': 'romania', 'name_ko': '루마니아', 'name_en': 'Romania', 'name_ja': 'ルーマニア', 'flag_cc': 'ro',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '루마니아는 <strong>Lege nr. 431/2023</strong>(다국적기업그룹 및 대규모 국내그룹의 글로벌 최저과세 보장에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Lege nr. 431/2023</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('루마니아에 모기업·자회사', '루마니아에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023', 'Lege nr. 431/2023 채택 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Agenția Națională de Administrare Fiscală (ANAF)', '루마니아 국세청', 'https://www.anaf.ro/'),
            ('Monitorul Oficial', '루마니아 공식 관보', 'https://monitoruloficial.ro/'),
        ],
    },

    'SI': {
        'slug': 'slovenia', 'name_ko': '슬로베니아', 'name_en': 'Slovenia', 'name_ja': 'スロベニア', 'flag_cc': 'si',
        'iir':   {'date': '2023-12-31', 'qualified': True},
        'utpr':  {'date': '2024-12-31', 'qualified': False},
        'qdmtt': {'date': '2023-12-31', 'qualified': True},
        'lead': '슬로베니아는 <strong>Zakon o minimalnem davku (ZMD)</strong>(최저세에 관한 법률)로 EU Directive 2022/2523을 자국 법령으로 도입했습니다. IIR과 QDMTT는 2023-12-31, UTPR은 2024-12-31 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Zakon o minimalnem davku (ZMD), Uradni list RS, št. 131/2023</strong>', 'EU Directive 2022/2523 transposition'),
        ],
        'insights': [
            ('슬로베니아에 모기업·자회사', '슬로베니아에 모기업·자회사를 둔 다국적기업그룹은 2023-12-31 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023', 'ZMD (Uradni list RS, št. 131/2023) 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('Finančna uprava Republike Slovenije (FURS)', '슬로베니아 국세청', 'https://www.fu.gov.si/'),
            ('Uradni list Republike Slovenije', '슬로베니아 공식 관보', 'https://www.uradni-list.si/'),
        ],
    },

    'TR': {
        'slug': 'turkey', 'name_ko': '튀르키예', 'name_en': 'Türkiye', 'name_ja': 'トルコ', 'flag_cc': 'tr',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': '2025-01-01', 'qualified': False},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '튀르키예는 <strong>5520 sayılı Kurumlar Vergisi Kanunu, Beşinci Kısım</strong>(법인세법 제5편 — 자국·글로벌 최저 보충 법인세)으로 OECD Pillar Two를 도입했습니다. IIR과 QDMTT는 2024-01-01, UTPR은 2025-01-01 이후 개시 사업연도부터 시행됩니다.',
        'domestic_laws': [
            ('<strong>Kanun Numarası 5520 (Kurumlar Vergisi Kanunu), Beşinci Kısım</strong>', '법인세법 제5편 — 자국 및 글로벌 최저 보충 법인세 도입'),
        ],
        'insights': [
            ('튀르키예에 모기업·자회사', '튀르키예에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2023', '법인세법 제5편 신설 — IIR · QDMTT 시행 (2024-01-01)'),
        ],
        'sources': [
            ('Gelir İdaresi Başkanlığı (GİB)', '튀르키예 국세청', 'https://www.gib.gov.tr/'),
            ('Resmî Gazete', '튀르키예 공식 관보', 'https://www.resmigazete.gov.tr/'),
        ],
    },

    'ZA': {
        'slug': 'south-africa', 'name_ko': '남아프리카공화국', 'name_en': 'South Africa', 'name_ja': '南アフリカ共和国', 'flag_cc': 'za',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '남아프리카공화국은 <strong>Global Minimum Tax Act (Act No. 46 of 2024)</strong>로 OECD Pillar Two의 IIR과 QDMTT를 도입했습니다. 시행일은 2024-01-01 이후 개시 사업연도이며, UTPR은 아직 별도로 발표되지 않은 상태입니다.',
        'domestic_laws': [
            ('<strong>Global Minimum Tax Act (Act No. 46 of 2024)</strong>', 'IIR + QDMTT 도입'),
        ],
        'insights': [
            ('남아공에 모기업·자회사', '남아공에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다.'),
        ],
        'recent': [
            ('2024', 'Global Minimum Tax Act (Act No. 46 of 2024) 공포 — IIR · QDMTT 시행'),
        ],
        'sources': [
            ('South African Revenue Service (SARS)', '남아공 국세청', 'https://www.sars.gov.za/'),
            ('Government Gazette', '남아공 공식 관보', 'https://www.gov.za/'),
        ],
    },

    'QA': {
        'slug': 'qatar', 'name_ko': '카타르', 'name_en': 'Qatar', 'name_ja': 'カタール', 'flag_cc': 'qa',
        'iir':   {'date': '2025-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2025-01-01', 'qualified': True},
        'lead': '카타르는 <strong>Law No. 22 of 2024</strong>(소득세법 일부개정)로 OECD Pillar Two의 IIR과 QDMTT를 도입했습니다. 시행일은 2025-01-01 이후 개시 사업연도이며, UTPR은 아직 별도로 발표되지 않은 상태입니다.',
        'domestic_laws': [
            ('<strong>Law No. 22 of 2024</strong>', 'Amending some provisions of the Income Tax Law (Law No. 24 of 2018) — IIR + QDMTT 도입'),
        ],
        'insights': [
            ('카타르에 모기업·자회사', '카타르에 모기업·자회사를 둔 다국적기업그룹은 2025-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. 카타르 표준 법인세율(10%)이 글로벌최저한세율(15%) 미만이므로 자회사 ETR이 임계치 하회하는 사례가 많아 사전 모델링이 중요합니다.'),
        ],
        'recent': [
            ('2024', 'Law No. 22 of 2024 공포 — IIR · QDMTT 시행 (2025-01-01)'),
        ],
        'sources': [
            ('General Tax Authority (GTA)', '카타르 국세청', 'https://www.gta.gov.qa/'),
            ('Al-Meezan (National Legislator)', '카타르 공식 법령 데이터베이스', 'https://www.almeezan.qa/'),
        ],
    },

    'LI': {
        'slug': 'liechtenstein', 'name_ko': '리히텐슈타인', 'name_en': 'Liechtenstein', 'name_ja': 'リヒテンシュタイン', 'flag_cc': 'li',
        'iir':   {'date': '2024-01-01', 'qualified': True},
        'utpr':  {'date': None, 'qualified': False, 'note': '도입 미발표'},
        'qdmtt': {'date': '2024-01-01', 'qualified': True},
        'lead': '리히텐슈타인은 <strong>GloBE-Gesetz (Gesetz vom 10. November 2023 über die Mindestbesteuerung grosser Unternehmensgruppen)</strong>로 OECD Pillar Two의 IIR과 QDMTT를 도입했습니다. 시행일은 2024-01-01 이후 개시 사업연도입니다.',
        'domestic_laws': [
            ('<strong>Gesetz vom 10. November 2023 über die Mindestbesteuerung grosser Unternehmensgruppen (GloBE-Gesetz)</strong>', 'IIR + QDMTT 도입. EFTA·EEA 회원국으로 OECD 모델규정 자체 도입'),
        ],
        'insights': [
            ('리히텐슈타인에 모기업·자회사', '리히텐슈타인에 모기업·자회사를 둔 다국적기업그룹은 2024-01-01 이후 개시 사업연도부터 IIR/QDMTT 적용 대상입니다. 리히텐슈타인 표준 법인세율(12.5%)이 글로벌최저한세율(15%) 미만이므로 자회사 ETR이 임계치 하회하는 사례가 많아 사전 모델링이 중요합니다.'),
        ],
        'recent': [
            ('2023-11-10', 'GloBE-Gesetz 공포 — IIR · QDMTT 시행 (2024-01-01)'),
        ],
        'sources': [
            ('Steuerverwaltung des Fürstentums Liechtenstein', '리히텐슈타인 세무청', 'https://www.llv.li/'),
            ('Liechtensteinisches Landesgesetzblatt (LGBl.)', '리히텐슈타인 공식 관보', 'https://www.gesetze.li/'),
        ],
    },
}


# ─────────────────────────────────────────────────────────────────
# HTML 생성
# ─────────────────────────────────────────────────────────────────

SENTRY_HEAD = '''<script src="https://js.sentry-cdn.com/ee4401caad2ce32f342a8993779fdf33.min.js" crossorigin="anonymous"></script>
<script>
window.sentryOnLoad = function () {
  Sentry.init({ tracesSampleRate: 0, replaysSessionSampleRate: 0, replaysOnErrorSampleRate: 0, sendDefaultPii: false,
    environment: location.hostname === 'pillartwo.app' ? 'production' : 'development',
    ignoreErrors: ['ResizeObserver loop completed', 'ResizeObserver loop limit exceeded', 'Non-Error promise rejection captured', 'Script error.', 'Load failed'],
    denyUrls: [/chrome-extension:\\/\\//i, /moz-extension:\\/\\//i, /googletagmanager\\.com/i, /clarity\\.ms/i, /google-analytics\\.com/i] });
};
</script>'''

BRAND_SVG = '<svg class="docs-brand-pillar" width="19" height="22" viewBox="0 0 19 22" aria-hidden="true"><rect x="0" y="0" width="9" height="2" rx=".5" fill="#2563eb"/><rect x="2.5" y="2.5" width="4" height="13.5" fill="#2563eb"/><rect x="1" y="16.5" width="7" height="1.5" rx=".3" fill="#2563eb"/><rect x="0" y="18.5" width="9" height="3" rx=".5" fill="#2563eb"/><rect x="10" y="0" width="9" height="2" rx=".5" fill="#4f46e5"/><rect x="12.5" y="2.5" width="4" height="13.5" fill="#4f46e5"/><rect x="11" y="16.5" width="7" height="1.5" rx=".3" fill="#4f46e5"/><rect x="10" y="18.5" width="9" height="3" rx=".5" fill="#4f46e5"/></svg>'


def render_tl_box(rule_label, date, detail_ko, sub=None, latest=False):
    """시행 타임라인 단일 카드."""
    if date is None:
        # 미도입 케이스 — 카드는 회색 톤
        cls = 'jr-tl-box jr-tl-box-none'
        date_html = '<span class="jr-tl-date jr-tl-date-none">—</span>'
    else:
        cls = 'jr-tl-box jr-tl-box-latest' if latest else 'jr-tl-box'
        date_html = f'<span class="jr-tl-date">{date}</span>'
    sub_html = f'<span class="jr-tl-subdetail">{sub}</span>' if sub else ''
    return f'''<div class="{cls}" role="listitem">
        <span class="jr-tl-rule">{rule_label}</span>
        {date_html}
        <span class="jr-tl-detail">{detail_ko}{sub_html}</span>
      </div>'''


def render_quick_row(rule_anchor, label, label_extra, sub, date_text, badge, tag=None):
    """Quick reference 표 한 행."""
    sub_html = f'<span class="jr-cell-sub">{sub}</span>' if sub else ''
    tag_html = f' <span class="{tag["cls"]}">{tag["text"]}</span>' if tag else ''
    return f'''        <tr>
          <td>
            <a href="/glossary#{rule_anchor}"><strong>{label}</strong></a>{f" — {label_extra}" if label_extra else ""}
            {sub_html}
          </td>
          <td>{date_text}</td>
          <td><span class="{badge["cls"]}">{badge["text"]}</span>{tag_html}</td>
        </tr>'''


# ─────────────────────────────────────────────────────────────────
# 다국어 (en / ja) — 템플릿 + 자동 narrative 구성
# 한국어 페이지(render_page)는 그대로 유지. en/ja는 render_page_intl로 분리.
# ─────────────────────────────────────────────────────────────────

T = {
    # 페이지 메타
    'meta.title_suffix': {'en': 'PillarTwo Architect', 'ja': 'PillarTwo Architect'},
    # 섹션 헤더
    'sec.timeline': {'en': 'Implementation Timeline', 'ja': '施行タイムライン'},
    'sec.quick': {'en': 'Quick reference', 'ja': 'クイックリファレンス'},
    'sec.laws': {'en': 'Implementing legislation', 'ja': '根拠法令'},
    'sec.impl': {'en': 'Practical implications', 'ja': '実務上の論点'},
    'sec.recent': {'en': 'Recent legislative developments', 'ja': '近時の法改正動向'},
    'sec.terms': {'en': 'Related terms', 'ja': '関連用語'},
    'sec.cta': {'en': 'Try this in PillarTwo Architect', 'ja': 'PillarTwo Architectで分析する'},
    'sec.sources': {'en': 'Sources', 'ja': '出典'},
    # 규정 풀네임 (OECD 표준)
    'rule.iir': {'en': 'Income Inclusion Rule', 'ja': '所得算入規則'},
    'rule.utpr': {'en': 'Undertaxed Profits Rule', 'ja': '軽課税所得規則'},
    'rule.qdmtt': {'en': 'Qualified Domestic Minimum Top-up Tax', 'ja': '適格国内ミニマム課税'},
    # Badge / Tag
    'badge.ok': {'en': 'In force', 'ja': '施行'},
    'badge.new': {'en': 'Newly in force', 'ja': '新規施行'},
    'badge.pending': {'en': 'Case-by-case', 'ja': '要検討'},
    'badge.none': {'en': 'Not adopted', 'ja': '未導入'},
    'tag.qualified': {'en': 'OECD qualified', 'ja': 'OECD適格認定'},
    'tag.pending': {'en': 'OECD review pending', 'ja': 'OECD適格性審査中'},
    # Table header
    'th.rule': {'en': 'Rule', 'ja': '規定'},
    'th.date': {'en': 'Effective date', 'ja': '施行日'},
    'th.status': {'en': 'Status', 'ja': 'ステータス'},
    # Date phrase template
    'date.from': {'en': 'Fiscal years beginning on or after {d}', 'ja': '{d}以降開始する会計年度'},
    'date.from_short': {'en': 'on or after {d}', 'ja': '{d}以降'},
    # Sub-line "국내 도입명"
    'sub.localname': {'en': 'Local name: {n}', 'ja': '現地名称：{n}'},
    # QDMTT SH row
    'qdmttsh.date': {'en': 'Available alongside the QDMTT', 'ja': 'QDMTT施行に合わせて適用可能'},
    # Timeline note
    'tl.note': {
        'en': 'Each rule applies to fiscal years <strong>beginning</strong> on or after the date shown.',
        'ja': '各規定は上記日付以降に<strong>開始する</strong>会計年度から適用されます。',
    },
    # CTA
    'cta.lead': {
        'en': 'Design a group with {country} entities together with PillarTwo Architect and see the full Pillar Two blueprint instantly.',
        'ja': '{country}の構成会社を含むグループをPillarTwo Architectと一緒に設計し、グローバル・ミニマム課税の青写真を即座に確認できます。',
    },
    'cta.btn.start': {'en': 'Start analysing →', 'ja': '分析を開始 →'},
    'cta.btn.overview': {'en': 'Pillar Two', 'ja': 'Pillar Two'},
    'cta.btn.about': {'en': 'About', 'ja': 'サービス紹介'},
    'cta.btn.glossary': {'en': 'Glossary', 'ja': '用語集'},
    # Nav
    'nav.home': {'en': '← Back to Architect', 'ja': '← アーキテクトに戻る'},
    'nav.overview': {'en': 'Pillar Two', 'ja': 'Pillar Two'},
    'nav.jurisdictions': {'en': 'Jurisdictions', 'ja': '国別状況'},
    'nav.about': {'en': 'About', 'ja': 'サービス紹介'},
    # Breadcrumb
    'crumb.jr': {'en': 'Jurisdictions', 'ja': '国別状況'},
    # Disclaimer
    'disc.h3': {'en': 'Disclaimer', 'ja': 'Disclaimer'},
    'disc.intro': {
        'en': 'This page is reference information prepared <strong>as of 2026-05-28</strong> by synthesising the primary sources listed above, and is not legal or tax advice. Before applying any of this material in practice, please:',
        'ja': '本ページは<strong>2026-05-28時点</strong>で上記1次資料を統合・整理した参考情報であり、法律・税務アドバイスではありません。実務に適用する前に必ず以下を行ってください：',
    },
    'disc.li1': {
        'en': 'Verify the latest legislation, administrative guidance, and tax authority notices',
        'ja': '最新の法令・行政解釈・税務当局の案内を確認すること',
    },
    'disc.li2': {
        'en': 'Obtain review by a qualified Pillar Two specialist',
        'ja': '有資格のPillar Two専門家のレビューを受けること',
    },
    'disc.li3': {
        'en': 'Reassess applicability against the specific facts and circumstances of the group',
        'ja': 'グループ固有の事実関係に照らして適用可否を再判断すること',
    },
    'disc.trans_label': {'en': '<strong>Translation note.</strong>', 'ja': '<strong>翻訳に関するご注意。</strong>'},
    'disc.trans_body': {
        'en': 'The authoritative version of this page is the Korean original (<a href="/jurisdictions/{slug}">국가별 현황 › {name_ko}</a>). This English version is provided for accessibility and may not capture every nuance of the original sources. Where precision matters, please refer to the Korean original or to the source legislation in its original language.',
        'ja': '本ページの正本は韓国語版（<a href="/jurisdictions/{slug}">国別状況 › {name_ko}</a>）です。日本語版はアクセシビリティを目的として提供されており、原資料のニュアンスを完全に反映していない場合があります。厳密な判断が必要な場面では、韓国語原文または該当法令の原語をご参照ください。',
    },
    'disc.stamp': {
        'en': 'Last verified: <time datetime="2026-05-28">2026-05-28</time> · OECD Central Record dated 1 May 2026',
        'ja': 'Last verified: <time datetime="2026-05-28">2026-05-28</time> · OECD Central Record dated 1 May 2026',
    },
    # Related terms
    'term.iir': {'en': 'Income Inclusion Rule (IIR)', 'ja': '所得算入規則 (IIR)'},
    'term.utpr': {'en': 'Undertaxed Profits Rule (UTPR)', 'ja': '軽課税所得規則 (UTPR)'},
    'term.qdmtt': {'en': 'QDMTT', 'ja': '適格国内ミニマム課税 (QDMTT)'},
    'term.qdmttsh': {'en': 'QDMTT Safe Harbour', 'ja': 'QDMTT Safe Harbour'},
    'term.topup': {'en': 'Top-up Tax', 'ja': '追加税額 (Top-up Tax)'},
    'term.etr': {'en': 'Effective Tax Rate (ETR)', 'ja': '実効税率 (ETR)'},
    'term.mne': {'en': 'MNE Group', 'ja': '多国籍企業グループ (MNE Group)'},
    # Footer
    'foot.home': {'en': '← Back to Architect', 'ja': '← アーキテクトに戻る'},
    'foot.overview': {'en': 'Pillar Two', 'ja': 'Pillar Two'},
    'foot.glossary': {'en': 'Glossary', 'ja': '用語集'},
    'foot.about': {'en': 'About', 'ja': 'サービス紹介'},
    # OG description template
    'og.desc': {
        'en': "{country}'s Pillar Two: IIR {iir}, UTPR {utpr}, QDMTT {qdmtt}.",
        'ja': "{country}のPillar Two: IIR {iir}、UTPR {utpr}、QDMTT {qdmtt}。",
    },
    # Meta description template
    'meta.desc': {
        'en': "{country}'s OECD Pillar Two adoption — IIR, UTPR, and QDMTT effective dates, implementing legislation, and practical implications.",
        'ja': "{country}のOECD Pillar Two導入状況 — IIR・UTPR・QDMTTの施行日、根拠法、実務上の留意点。",
    },
}


AUTO_TR = {
    'en': {
        # 시행/공포 류
        '이후 개시 사업연도부터 시행': 'in force from fiscal years beginning on or after the date shown',
        '이후 개시 사업연도부터': 'from fiscal years beginning on or after',
        '이후 개시 사업연도': 'fiscal years beginning on or after',
        '동시 시행': 'simultaneously in force',
        '동시': 'simultaneously',
        '관보 게재': 'published in the official gazette',
        '시행과 동일': 'effective alongside',
        '시행과 동일.': 'effective alongside.',
        # 행위/상태
        '공포': 'promulgated',
        '채택': 'adopted',
        '시행': 'in force',
        '신설': 'introduced',
        '도입 미발표': 'not yet announced',
        '도입': 'introduction',
        '미발표': 'not announced',
        '개정': 'amendment',
        '발표': 'announcement',
        '보도자료': 'press releases',
        '안내': 'guidance',
        # 기관·문서
        '국세청': 'Tax Authority',
        '재무부': 'Ministry of Finance',
        '연방재무부': 'Federal Ministry of Finance',
        '연방세무청': 'Federal Tax Authority',
        '연방국세청': 'Federal Tax Service',
        '관보': 'official gazette',
        '공식 관보': 'official gazette',
        '공식 법령 데이터베이스': 'official legislation database',
        '법령 데이터베이스': 'legislation database',
        '국가법령정보센터': 'Korea Law Information Center',
        # 연결사
        '및': 'and',
        # Pillar Two
        '글로벌 최저과세': 'Global Minimum Tax',
        '글로벌최저한세': 'Global Minimum Tax',
        '법인세법': 'Corporate Income Tax Act',
        '특정기준법인세액': 'specific reference corporate tax',
        '국제최저과세액': 'International Minimum Tax Amount',
        '국내최저과세액': 'Domestic Minimum Tax Amount',
        '추가': 'additional',
        '관련된': 'related',
        '제3장': 'Chapter 3',
        '제4장': 'Chapter 4',
        '제5장': 'Chapter 5',
        # 국가 demonym
        '독일': 'Germany',
        '프랑스': 'France',
        '이탈리아': 'Italy',
        '네덜란드': 'Netherlands',
        '스위스': 'Switzerland',
        '오스트리아': 'Austria',
        '아일랜드': 'Ireland',
        '룩셈부르크': 'Luxembourg',
        '벨기에': 'Belgium',
        '스페인': 'Spain',
        '스웨덴': 'Sweden',
        '폴란드': 'Poland',
        '헝가리': 'Hungary',
        '체코': 'Czechia',
        '덴마크': 'Denmark',
        '핀란드': 'Finland',
        '노르웨이': 'Norway',
        '포르투갈': 'Portugal',
        '그리스': 'Greece',
        '루마니아': 'Romania',
        '슬로베니아': 'Slovenia',
        '튀르키예': 'Türkiye',
        '캐나다': 'Canada',
        '브라질': 'Brazil',
        '남아프리카공화국': 'South Africa',
        '남아공': 'South Africa',
        '아랍에미리트': 'United Arab Emirates',
        '카타르': 'Qatar',
        '리히텐슈타인': 'Liechtenstein',
        '싱가포르': 'Singapore',
        '호주': 'Australia',
        '홍콩': 'Hong Kong',
        '베트남': 'Vietnam',
        '인도네시아': 'Indonesia',
        '말레이시아': 'Malaysia',
        '태국': 'Thailand',
        '뉴질랜드': 'New Zealand',
        '일본': 'Japan',
        '미국': 'United States',
        '영국': 'United Kingdom',
        '대한민국': 'Korea',
        '한국': 'Korea',
    },
    'ja': {
        # 시행/공포 류
        '이후 개시 사업연도부터 시행': '以降開始する会計年度から施行',
        '이후 개시 사업연도부터': '以降開始する会計年度から',
        '이후 개시 사업연도': '以降開始する会計年度',
        '동시 시행': '同時施行',
        '동시': '同時',
        '관보 게재': '官報掲載',
        '시행과 동일': '施行と同日',
        # 행위/상태
        '공포': '公布',
        '채택': '採択',
        '시행': '施行',
        '신설': '新設',
        '도입 미발표': '未発表',
        '도입': '導入',
        '미발표': '未発表',
        '개정': '改正',
        '발표': '発表',
        '보도자료': '報道資料',
        '안내': '案内',
        # 기관·문서
        '국세청': '国税庁',
        '재무부': '財務省',
        '연방재무부': '連邦財務省',
        '연방세무청': '連邦税務庁',
        '연방국세청': '連邦税務局',
        '관보': '官報',
        '공식 관보': '官報',
        '공식 법령 데이터베이스': '法令データベース',
        '법령 데이터베이스': '法令データベース',
        '국가법령정보센터': '国家法令情報センター',
        # 연결사
        '및': 'および',
        # Pillar Two
        '글로벌 최저과세': 'グローバル・ミニマム課税',
        '글로벌최저한세': 'グローバル・ミニマム課税',
        '법인세법': '法人税法',
        '제3장': '第3章',
        '제4장': '第4章',
        '제5장': '第5章',
        # 국가 demonym
        '독일': 'ドイツ',
        '프랑스': 'フランス',
        '이탈리아': 'イタリア',
        '네덜란드': 'オランダ',
        '스위스': 'スイス',
        '오스트리아': 'オーストリア',
        '아일랜드': 'アイルランド',
        '룩셈부르크': 'ルクセンブルク',
        '벨기에': 'ベルギー',
        '스페인': 'スペイン',
        '스웨덴': 'スウェーデン',
        '폴란드': 'ポーランド',
        '헝가리': 'ハンガリー',
        '체코': 'チェコ',
        '덴마크': 'デンマーク',
        '핀란드': 'フィンランド',
        '노르웨이': 'ノルウェー',
        '포르투갈': 'ポルトガル',
        '그리스': 'ギリシャ',
        '루마니아': 'ルーマニア',
        '슬로베니아': 'スロベニア',
        '튀르키예': 'トルコ',
        '캐나다': 'カナダ',
        '브라질': 'ブラジル',
        '남아프리카공화국': '南アフリカ共和国',
        '남아공': '南アフリカ',
        '아랍에미리트': 'アラブ首長国連邦',
        '카타르': 'カタール',
        '리히텐슈타인': 'リヒテンシュタイン',
        '싱가포르': 'シンガポール',
        '호주': 'オーストラリア',
        '홍콩': '香港',
        '베트남': 'ベトナム',
        '인도네시아': 'インドネシア',
        '말레이시아': 'マレーシア',
        '태국': 'タイ',
        '뉴질랜드': 'ニュージーランド',
        '일본': '日本',
        '미국': 'アメリカ',
        '영국': 'イギリス',
        '대한민국': '韓国',
        '한국': '韓国',
    },
}


def auto_tr(text, lang):
    """Korean 공통 단어를 en/ja로 자동 치환. lang='ko'면 그대로."""
    if lang == 'ko' or not text:
        return text
    out = text
    for k, v in AUTO_TR.get(lang, {}).items():
        out = out.replace(k, v)
    return out


def t(key, lang, **vars):
    """템플릿 lookup with var substitution"""
    s = T.get(key, {}).get(lang, key)
    for k, v in vars.items():
        s = s.replace('{' + k + '}', str(v))
    return s


def fmt_date_from(date, lang):
    if not date:
        return '—'
    return t('date.from', lang, d=date)


def fmt_date_from_short(date, lang):
    if not date:
        return '—'
    return t('date.from_short', lang, d=date)


def country_name(data, lang):
    if lang == 'en':
        return data['name_en']
    if lang == 'ja':
        return data['name_ja']
    return data['name_ko']


def get_lang_field(data, field, lang, fallback=None):
    """국가 데이터에서 lang-aware 필드 가져오기. {field}_{lang} 우선, 없으면 fallback or 한국어."""
    key = f'{field}_{lang}'
    if key in data:
        return data[key]
    if fallback is not None:
        return fallback
    return data.get(field, '')


def render_tl_box_intl(rule_label, date, detail, sub=None, latest=False):
    if date is None:
        cls = 'jr-tl-box jr-tl-box-none'
        date_html = '<span class="jr-tl-date jr-tl-date-none">—</span>'
    else:
        cls = 'jr-tl-box jr-tl-box-latest' if latest else 'jr-tl-box'
        date_html = f'<span class="jr-tl-date">{date}</span>'
    sub_html = f'<span class="jr-tl-subdetail">{sub}</span>' if sub else ''
    return f'''<div class="{cls}" role="listitem">
        <span class="jr-tl-rule">{rule_label}</span>
        {date_html}
        <span class="jr-tl-detail">{detail}{sub_html}</span>
      </div>'''


def render_quick_row_intl(rule_anchor, label, label_extra, sub, date_text, badge, tag=None):
    sub_html = f'<span class="jr-cell-sub">{sub}</span>' if sub else ''
    tag_html = f' <span class="{tag["cls"]}">{tag["text"]}</span>' if tag else ''
    return f'''        <tr>
          <td>
            <a href="/glossary#{rule_anchor}"><strong>{label}</strong></a>{f" — {label_extra}" if label_extra else ""}
            {sub_html}
          </td>
          <td>{date_text}</td>
          <td><span class="{badge["cls"]}">{badge["text"]}</span>{tag_html}</td>
        </tr>'''


def build_lead_default(data, lang):
    """국가 데이터에 lead_{lang} 없을 때 자동 생성하는 기본 lead."""
    country = country_name(data, lang)
    iir = data['iir']
    utpr = data['utpr']
    qdmtt = data['qdmtt']
    # Find main law name from domestic_laws first entry
    laws = get_lang_field(data, 'domestic_laws', lang, fallback=data.get('domestic_laws', []))
    law_html = laws[0][0] if laws else ''
    iir_d = iir.get('date'); utpr_d = utpr.get('date'); qdmtt_d = qdmtt.get('date')
    if lang == 'en':
        parts = [f"{country} has implemented OECD Pillar Two through {law_html}."]
        rules = []
        if iir_d: rules.append(f"the IIR from {iir_d}")
        if qdmtt_d: rules.append(f"the QDMTT from {qdmtt_d}")
        if utpr_d: rules.append(f"the UTPR from {utpr_d}")
        if rules:
            parts.append("Each applies to fiscal years beginning on or after the respective date: " + ", ".join(rules) + ".")
        return ' '.join(parts)
    if lang == 'ja':
        parts = [f"{country}は{law_html}によりOECDのPillar Twoを導入しています。"]
        rules = []
        if iir_d: rules.append(f"IIR：{iir_d}以降")
        if qdmtt_d: rules.append(f"QDMTT：{qdmtt_d}以降")
        if utpr_d: rules.append(f"UTPR：{utpr_d}以降")
        if rules:
            parts.append("各規定はそれぞれの日付以降に開始する会計年度から適用されます（" + "、".join(rules) + "）。")
        return ' '.join(parts)
    return ''


def build_insights_default(data, lang):
    """국가 데이터에 insights_{lang} 없을 때 자동 생성하는 기본 insights."""
    country = country_name(data, lang)
    iir = data['iir']
    qdmtt = data['qdmtt']
    paras = []
    if lang == 'en':
        if iir.get('date'):
            paras.append(f"<strong>MNE groups parented in {country}</strong> are subject to the IIR for fiscal years beginning on or after {iir['date']}. Where a subsidiary's jurisdictional effective tax rate (ETR) falls below 15%, top-up tax is computed and paid in {country} (as the jurisdiction of the parent entities), and the group must also file the GloBE Information Return (GIR).")
        if qdmtt.get('date'):
            paras.append(f"<strong>MNE groups with constituent entities in {country}</strong> are subject to {country}'s QDMTT for fiscal years beginning on or after {qdmtt['date']}. Where the conditions of the QDMTT Safe Harbour are met, the IIR/UTPR computation at the parent jurisdictions may be exempted, reducing the burden of dual computation.")
    if lang == 'ja':
        if iir.get('date'):
            paras.append(f"<strong>{country}に親会社を置く多国籍企業グループ</strong>は、{iir['date']}以降開始する会計年度からIIRの対象となります。子会社所在地国の国別実効税率(ETR)が15%未満の場合、親会社等の所在地国（{country}）でIIRに基づき追加税額を申告・納付する必要があり、GloBE情報申告書(GIR)の提出義務も併せて発生します。")
        if qdmtt.get('date'):
            paras.append(f"<strong>{country}に子会社を置く多国籍企業グループ</strong>は、{qdmtt['date']}以降開始する会計年度から{country}のQDMTTの対象となります。QDMTT Safe Harbourの適用要件を満たせば、親会社等の所在地国におけるIIR/UTPR計算が免除される可能性があり、二重コンプライアンス負担の軽減につながります。")
    return paras


def render_page_intl(cc, data, lang):
    """en / ja 페이지 렌더. ko는 기존 render_page 사용."""
    iir = data['iir']
    utpr = data['utpr']
    qdmtt = data['qdmtt']
    slug = data['slug']
    name_ko = data['name_ko']
    name_en = data['name_en']
    name_ja = data['name_ja']
    country = country_name(data, lang)

    # Timeline
    items = [
        ('IIR',   iir['date'],   t('rule.iir', lang),   iir.get('domestic_name')),
        ('UTPR',  utpr['date'],  t('rule.utpr', lang),  utpr.get('domestic_name')),
        ('QDMTT', qdmtt['date'], t('rule.qdmtt', lang), qdmtt.get('domestic_name')),
    ]
    dated_only = [it for it in items if it[1]]
    max_date = max(it[1] for it in dated_only) if dated_only else None
    tl_parts = []
    for i, (label, date, detail, sub) in enumerate(items):
        if i > 0:
            tl_parts.append('<div class="jr-tl-connector" aria-hidden="true"></div>')
        is_latest = (date is not None and date == max_date)
        sub_text = t('sub.localname', lang, n=sub) if sub else None
        tl_parts.append(render_tl_box_intl(label, date, detail, sub_text, latest=is_latest))
    tl_html = '\n      '.join(tl_parts)

    # Quick reference
    def badge_ok(): return {'cls': 'jr-badge jr-badge-ok', 'text': t('badge.ok', lang)}
    def badge_new(): return {'cls': 'jr-badge jr-badge-new', 'text': t('badge.new', lang)}
    def badge_pending(): return {'cls': 'jr-badge jr-badge-pending', 'text': t('badge.pending', lang)}
    def badge_none_(text=None): return {'cls': 'jr-badge jr-badge-none', 'text': text or t('badge.none', lang)}
    def tag_qual(): return {'cls': 'jr-tag', 'text': t('tag.qualified', lang)}
    def tag_pend(): return {'cls': 'jr-tag jr-tag-pending', 'text': t('tag.pending', lang)}

    rows = []
    # IIR
    if iir.get('date'):
        sub_iir = t('sub.localname', lang, n=iir['domestic_name']) if iir.get('domestic_name') else None
        rows.append(render_quick_row_intl('iir', 'IIR', t('rule.iir', lang), sub_iir,
            fmt_date_from(iir['date'], lang), badge_ok(),
            tag_qual() if iir.get('qualified') else tag_pend()))
    else:
        rows.append(render_quick_row_intl('iir', 'IIR', t('rule.iir', lang), None,
            '—', badge_none_(), None))
    # UTPR
    if utpr.get('date'):
        rows.append(render_quick_row_intl('utpr', 'UTPR', t('rule.utpr', lang), None,
            fmt_date_from(utpr['date'], lang), badge_ok(),
            tag_qual() if utpr.get('qualified') else tag_pend()))
    else:
        rows.append(render_quick_row_intl('utpr', 'UTPR', t('rule.utpr', lang), None,
            '—', badge_none_(), None))
    # QDMTT
    if qdmtt.get('date'):
        sub_q = t('sub.localname', lang, n=qdmtt['domestic_name']) if qdmtt.get('domestic_name') else None
        is_new = (max_date == qdmtt['date'])
        rows.append(render_quick_row_intl('qdmtt', 'QDMTT', t('rule.qdmtt', lang), sub_q,
            fmt_date_from(qdmtt['date'], lang),
            badge_new() if is_new else badge_ok(),
            tag_qual() if qdmtt.get('qualified') else tag_pend()))
    else:
        rows.append(render_quick_row_intl('qdmtt', 'QDMTT', t('rule.qdmtt', lang), None,
            '—', badge_none_(), None))
    # QDMTT SH
    rows.append(f'''        <tr>
          <td><a href="/glossary#qdmttsh"><strong>QDMTT Safe Harbour</strong></a></td>
          <td>{t('qdmttsh.date', lang)}</td>
          <td><span class="jr-badge jr-badge-pending">{t('badge.pending', lang)}</span></td>
        </tr>''')
    quick_html = '\n'.join(rows)

    # Lead
    lead = get_lang_field(data, 'lead', lang, fallback=build_lead_default(data, lang))

    # Domestic laws — try lang-aware override, fallback auto-translate
    laws_override = data.get(f'domestic_laws_{lang}')
    laws = laws_override if laws_override else data.get('domestic_laws', [])
    laws_html = '\n'.join(
        f'      <li>{name} — {auto_tr(detail, lang) if not laws_override else detail}</li>' if detail else f'      <li>{name}</li>'
        for name, detail in laws
    )

    # Insights — lang override or default template
    insights_override = data.get(f'insights_{lang}')
    if insights_override:
        insights_paras = [text for _, text in insights_override]
    else:
        insights_paras = build_insights_default(data, lang)
    insights_html = '\n'.join(f'    <p>{p}</p>' for p in insights_paras)

    # Recent — try lang-aware override, fallback auto-translate
    recent_override = data.get(f'recent_{lang}')
    recent = recent_override if recent_override else data.get('recent', [])
    recent_html = '\n'.join(
        f'      <li><strong>{date}</strong>: {auto_tr(event, lang) if not recent_override else event}</li>'
        for date, event in recent
    )

    # Sources — try lang-aware override, fallback auto-translate
    sources_override = data.get(f'sources_{lang}')
    sources = sources_override if sources_override else data.get('sources', [])
    src_lines = []
    for src in sources:
        if len(src) == 3:
            name, detail, url = src
            link = f' <a href="{url}" rel="external nofollow">{url.split("//")[-1].rstrip("/")[:40]}{"..." if len(url.split("//")[-1].rstrip("/")) > 40 else ""}</a>'
        else:
            name, detail = src[0], src[1]
            link = ''
        if not sources_override:
            name = auto_tr(name, lang)
            detail = auto_tr(detail, lang)
        src_lines.append(f'      <li><strong>{name}</strong> — {detail}.{link}</li>')
    oecd_src_en = ('      <li>\n'
                   '        <strong>OECD Inclusive Framework</strong> — Updated Central Record for Purposes of the\n'
                   '        Global Minimum Tax, approved 2026-05-11 (current as at 2026-05-01).\n'
                   '        <a href="https://www.oecd.org/en/topics/policy-sub-issues/global-minimum-tax/" rel="external nofollow">OECD Global Minimum Tax</a>\n'
                   '      </li>')
    oecd_src_ja = ('      <li>\n'
                   '        <strong>OECD/G20包摂的枠組み(Inclusive Framework)</strong> — Updated Central Record for Purposes of\n'
                   '        the Global Minimum Tax、2026-05-11承認（2026-05-01時点）。\n'
                   '        <a href="https://www.oecd.org/en/topics/policy-sub-issues/global-minimum-tax/" rel="external nofollow">OECDグローバル・ミニマム課税ページ</a>\n'
                   '      </li>')
    oecd_src = oecd_src_en if lang == 'en' else oecd_src_ja
    sources_html = oecd_src + '\n' + '\n'.join(src_lines)

    # CTA paragraph
    cta_p = t('cta.lead', lang, country=country)

    # Disclaimer (incl translation note)
    disc_html = f'''<p>
        {t('disc.intro', lang)}
      </p>
      <ul>
        <li>{t('disc.li1', lang)}</li>
        <li>{t('disc.li2', lang)}</li>
        <li>{t('disc.li3', lang)}</li>
      </ul>
      <p class="jr-disclaimer-trans">
        {t('disc.trans_label', lang)} {t('disc.trans_body', lang, slug=slug, name_ko=name_ko)}
      </p>
      <p class="jr-meta-stamp">
        {t('disc.stamp', lang)}
      </p>'''

    # OG / meta
    og_iir = iir.get('date') or ('—' if lang == 'en' else '—')
    og_utpr = utpr.get('date') or ('—' if lang == 'en' else '—')
    og_qdmtt = qdmtt.get('date') or ('—' if lang == 'en' else '—')
    og_desc = t('og.desc', lang, country=country, iir=og_iir, utpr=og_utpr, qdmtt=og_qdmtt)
    meta_desc = t('meta.desc', lang, country=country)

    # Page title
    law_short = data.get('law_short')
    if lang == 'en':
        title = f'Pillar Two in {country} — {law_short} | PillarTwo Architect' if law_short else f'Pillar Two in {country} | PillarTwo Architect'
        og_title = f'Pillar Two in {country}' + (f' — {law_short}' if law_short else '')
    else:
        law_short_ja = data.get('law_short_ja')
        title = f'{country}のPillar Two — {law_short_ja} | PillarTwo Architect' if law_short_ja else f'{country}のPillar Two | PillarTwo Architect'
        og_title = f'{country}のPillar Two' + (f' — {law_short_ja}' if law_short_ja else '')

    # URL paths
    canonical = f'https://pillartwo.app/jurisdictions/{lang}/{slug}'
    hreflang_ko = f'https://pillartwo.app/jurisdictions/{slug}'
    hreflang_en = f'https://pillartwo.app/jurisdictions/en/{slug}'
    hreflang_ja = f'https://pillartwo.app/jurisdictions/ja/{slug}'

    # Cross-lang script
    cross_lang_js = f'''
    document.querySelectorAll('.docs-lang-btn').forEach(b=>{{
      b.classList.toggle('active', b.dataset.lang===lang);
      b.addEventListener('click',()=>{{
        const nl=b.dataset.lang;
        try{{ localStorage.setItem('p2a.lang', nl); }}catch(e){{}}
        if(nl==='ko') location.href='/jurisdictions/{slug}';
        else if(nl==='en') location.href='/jurisdictions/en/{slug}';
        else if(nl==='ja') location.href='/jurisdictions/ja/{slug}';
        else setLang(nl);
      }});
    }});'''

    html_lang_attr = lang
    og_locale = 'en_US' if lang == 'en' else 'ja_JP'

    return f'''<!DOCTYPE html>
<html lang="{html_lang_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta name="robots" content="index, follow">
<meta name="naver-site-verification" content="03dcd7169d0affc69d6ebf2e0a2af01dd5694073" />
<meta name="naver-site-verification" content="b15c8fd7be4aab298a81448b4c4e346fc613d30a" />
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko" href="{hreflang_ko}">
<link rel="alternate" hreflang="en" href="{hreflang_en}">
<link rel="alternate" hreflang="ja" href="{hreflang_ja}">
<link rel="alternate" hreflang="x-default" href="{hreflang_ko}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "PillarTwo Architect", "item": "https://pillartwo.app/" }},
    {{ "@type": "ListItem", "position": 2, "name": "Jurisdictions", "item": "https://pillartwo.app/jurisdictions/" }},
    {{ "@type": "ListItem", "position": 3, "name": "{country}", "item": "{canonical}" }}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Pillar Two in {country} — Adoption Status, Effective Dates, and Implications" if False else "Pillar Two in {country}",
  "description": "{meta_desc}",
  "image": "https://pillartwo.app/og-image.png",
  "datePublished": "2026-05-28",
  "dateModified": "2026-05-28",
  "inLanguage": "{lang}",
  "author": {{ "@type": "Organization", "name": "PillarTwo Architect" }},
  "publisher": {{ "@type": "Organization", "name": "PillarTwo Architect", "url": "https://pillartwo.app" }},
  "mainEntityOfPage": "{canonical}",
  "about": [
    {{ "@type": "Country", "name": "{name_en}", "alternateName": ["{name_ko}", "{name_ja}"] }},
    {{ "@type": "Thing", "name": "OECD Pillar Two GloBE Rules" }}
  ],
  "citation": [
    {{ "@type": "CreativeWork", "name": "OECD Updated Central Record for Purposes of the Global Minimum Tax", "datePublished": "2026-05-11", "url": "https://www.oecd.org/en/topics/sub-issues/global-minimum-tax/" }}
  ]
}}
</script>
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://pillartwo.app/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{og_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="https://pillartwo.app/og-image.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#2563eb">
{SENTRY_HEAD}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/docs.css">
<link rel="stylesheet" href="/jurisdictions/jurisdictions.css">
</head>
<body class="docs-body">

<nav class="docs-nav">
  <a class="docs-brand" href="/">
    {BRAND_SVG}
    <span class="docs-brand-name">Pillar<em>Two</em></span>
    <span class="docs-brand-sub">Architect</span>
  </a>
  <div class="docs-nav-links">
    <a href="/">{t('nav.home', lang)}</a>
    <a href="/overview.html">{t('nav.overview', lang)}</a>
    <a href="/jurisdictions/" class="active">{t('nav.jurisdictions', lang)}</a>
    <a href="/about.html">{t('nav.about', lang)}</a>
  </div>
</nav>

<main class="docs-main">

  <header class="docs-hero">
    <div class="jr-breadcrumb">
      <a href="/jurisdictions/">{t('crumb.jr', lang)}</a> <span>›</span> {country}
    </div>
    <h1 class="jr-h1">
      <img class="jr-flag-img" src="https://flagcdn.com/w80/{data['flag_cc']}.png" srcset="https://flagcdn.com/w160/{data['flag_cc']}.png 2x" width="40" height="30" alt="{country}" loading="lazy">
      Pillar Two in {country}
    </h1>
    <p class="docs-lead">
      {lead}
    </p>
  </header>

  <section class="docs-section jr-tl-section">
    <h2>{t('sec.timeline', lang)}</h2>
    <div class="jr-timeline" role="list">
      {tl_html}
    </div>
    <p class="jr-tl-note">{t('tl.note', lang)}</p>
  </section>

  <section class="docs-section">
    <h2>{t('sec.quick', lang)}</h2>
    <table class="jr-quick">
      <thead>
        <tr><th>{t('th.rule', lang)}</th><th>{t('th.date', lang)}</th><th>{t('th.status', lang)}</th></tr>
      </thead>
      <tbody>
{quick_html}
      </tbody>
    </table>
  </section>

  <section class="docs-section">
    <h2>{t('sec.laws', lang)}</h2>
    <ul class="docs-list jr-laws">
{laws_html}
    </ul>
  </section>

  <section class="docs-section">
    <h2>{t('sec.impl', lang)}</h2>
{insights_html}
  </section>

  <section class="docs-section">
    <h2>{t('sec.recent', lang)}</h2>
    <ul class="docs-list">
{recent_html}
    </ul>
  </section>

  <section class="docs-section">
    <h2>{t('sec.terms', lang)}</h2>
    <div class="jr-related-terms">
      <a href="/glossary#iir" class="jr-term-chip">{t('term.iir', lang)}</a>
      <a href="/glossary#utpr" class="jr-term-chip">{t('term.utpr', lang)}</a>
      <a href="/glossary#qdmtt" class="jr-term-chip">{t('term.qdmtt', lang)}</a>
      <a href="/glossary#qdmttsh" class="jr-term-chip">{t('term.qdmttsh', lang)}</a>
      <a href="/glossary#topup" class="jr-term-chip">{t('term.topup', lang)}</a>
      <a href="/glossary#etr" class="jr-term-chip">{t('term.etr', lang)}</a>
      <a href="/glossary#mne" class="jr-term-chip">{t('term.mne', lang)}</a>
    </div>
  </section>

  <section class="docs-section jr-cta-section">
    <h2>{t('sec.cta', lang)}</h2>
    <p>{cta_p}</p>
    <a href="/" class="docs-btn primary">{t('cta.btn.start', lang)}</a>
    <a href="/overview.html" class="docs-btn ghost">{t('cta.btn.overview', lang)}</a>
    <a href="/about.html" class="docs-btn ghost">{t('cta.btn.about', lang)}</a>
    <a href="/glossary" class="docs-btn ghost">{t('cta.btn.glossary', lang)}</a>
  </section>

  <section class="docs-section jr-sources">
    <h2>{t('sec.sources', lang)}</h2>
    <ul class="docs-list">
{sources_html}
    </ul>
  </section>

  <section class="docs-section jr-disclaimer-section">
    <div class="jr-disclaimer">
      <h3>{t('disc.h3', lang)}</h3>
      {disc_html}
    </div>
  </section>

</main>

<footer class="docs-footer">
  <div class="docs-footer-inner">
    <span>© PillarTwo Architect</span>
    <span class="docs-footer-sep">·</span>
    <a href="/">{t('foot.home', lang)}</a>
    <span class="docs-footer-sep">·</span>
    <a href="/overview.html">{t('foot.overview', lang)}</a>
    <span class="docs-footer-sep">·</span>
    <a href="/glossary">{t('foot.glossary', lang)}</a>
    <span class="docs-footer-sep">·</span>
    <a href="/about.html">{t('foot.about', lang)}</a>
  </div>
</footer>

<div class="docs-lang-toggle">
  <button class="docs-lang-btn" data-lang="en">English</button>
  <button class="docs-lang-btn" data-lang="ko">한국어</button>
  <button class="docs-lang-btn" data-lang="ja">日本語</button>
</div>

<script src="/translations.min.js"></script>
<script>
  (function(){{
    let lang='{lang}';
    try{{ const saved=localStorage.getItem('p2a.lang'); if(saved==='ko'||saved==='en'||saved==='ja') lang=saved; }}catch(e){{}}
    setLang(lang);{cross_lang_js}
  }})();
</script>

</body>
</html>
'''


def render_page(cc, data):
    iir = data['iir']
    utpr = data['utpr']
    qdmtt = data['qdmtt']
    slug = data['slug']
    name_ko = data['name_ko']
    name_en = data['name_en']

    # ── Timeline cards (최신 시행이 가장 큰 날짜 = latest box)
    rules = []
    if iir['date']:
        rules.append((iir['date'], 'IIR', '소득산입규칙', iir.get('domestic_name')))
    if utpr['date']:
        rules.append((utpr['date'], 'UTPR', '소득산입보완규칙', utpr.get('domestic_name')))
    if qdmtt['date']:
        rules.append((qdmtt['date'], 'QDMTT', '적격소재국추가세', qdmtt.get('domestic_name')))

    # Timeline 3 카드 IIR/UTPR/QDMTT 순서 일관. None인 경우 미도입 카드.
    items = [
        ('IIR',   iir['date'],   '소득산입규칙',     iir.get('domestic_name')),
        ('UTPR',  utpr['date'],  '소득산입보완규칙', utpr.get('domestic_name')),
        ('QDMTT', qdmtt['date'], '적격소재국추가세', qdmtt.get('domestic_name')),
    ]
    dated_only = [it for it in items if it[1]]
    max_date = max(it[1] for it in dated_only) if dated_only else None
    tl_html_parts = []
    for i, (label, date, detail, sub) in enumerate(items):
        if i > 0:
            tl_html_parts.append('<div class="jr-tl-connector" aria-hidden="true"></div>')
        is_latest = (date is not None and date == max_date)
        sub_text = f'국내 도입명: {sub}' if sub else None
        tl_html_parts.append(render_tl_box(label, date, detail, sub_text, latest=is_latest))

    tl_html = '\n      '.join(tl_html_parts)

    # ── Quick reference rows
    def badge_ok(t='시행'): return {'cls': 'jr-badge jr-badge-ok', 'text': t}
    def badge_new(t='신규 시행'): return {'cls': 'jr-badge jr-badge-new', 'text': t}
    def badge_pending(t='검토 필요'): return {'cls': 'jr-badge jr-badge-pending', 'text': t}
    def badge_none(t='미도입'): return {'cls': 'jr-badge jr-badge-none', 'text': t}
    def tag_qual(): return {'cls': 'jr-tag', 'text': 'OECD 적격 인정'}
    def tag_pending(): return {'cls': 'jr-tag jr-tag-pending', 'text': 'OECD 적격 평가 중'}

    rows = []
    # IIR
    if iir['date']:
        rows.append(render_quick_row(
            'iir', 'IIR', '소득산입규칙',
            f"국내 도입명: {iir['domestic_name']}" if iir.get('domestic_name') else None,
            f"{iir['date']} 이후 개시 사업연도",
            badge_ok(),
            tag_qual() if iir.get('qualified') else tag_pending(),
        ))
    else:
        rows.append(render_quick_row(
            'iir', 'IIR', '소득산입규칙', None,
            '—', badge_none(iir.get('note', '도입 미발표')), None,
        ))
    # UTPR
    if utpr['date']:
        rows.append(render_quick_row(
            'utpr', 'UTPR', '소득산입보완규칙', None,
            f"{utpr['date']} 이후 개시 사업연도",
            badge_ok(),
            tag_qual() if utpr.get('qualified') else tag_pending(),
        ))
    else:
        rows.append(render_quick_row(
            'utpr', 'UTPR', '소득산입보완규칙', None,
            '—', badge_none(utpr.get('note', '도입 미발표')), None,
        ))
    # QDMTT
    if qdmtt['date']:
        rows.append(render_quick_row(
            'qdmtt', 'QDMTT', '적격소재국추가세',
            f"국내 도입명: {qdmtt['domestic_name']}" if qdmtt.get('domestic_name') else None,
            f"{qdmtt['date']} 이후 개시 사업연도",
            badge_ok(),
            tag_qual() if qdmtt.get('qualified') else tag_pending(),
        ))
    else:
        rows.append(render_quick_row(
            'qdmtt', 'QDMTT', '적격소재국추가세', None,
            '—', badge_none(qdmtt.get('note', '도입 미발표')), None,
        ))
    # QDMTT Safe Harbour — 일률
    rows.append('''        <tr>
          <td><a href="/glossary#qdmttsh"><strong>QDMTT Safe Harbour</strong></a></td>
          <td>QDMTT 시행에 맞추어 적용 가능</td>
          <td><span class="jr-badge jr-badge-pending">검토 필요</span></td>
        </tr>''')

    quick_html = '\n'.join(rows)

    # ── Domestic laws
    laws_html = '\n'.join(
        f'      <li>{name} — {detail}</li>' if detail else f'      <li>{name}</li>'
        for name, detail in data['domestic_laws']
    )

    # ── Insights
    insights_html = '\n'.join(
        f'    <p><strong>{name_ko + (" — " + label if not label.startswith(name_ko) else "")}</strong>: {text}</p>'
        if False else  # disable name prefix for now
        f'    <p>{text}</p>'
        for label, text in data['insights']
    )
    # Make first paragraph use a stronger lead-in
    insights_paragraphs = []
    for label, text in data['insights']:
        insights_paragraphs.append(f'    <p>{text}</p>')
    insights_html = '\n'.join(insights_paragraphs)

    # ── Recent legislation
    recent_html = '\n'.join(
        f'      <li><strong>{date}</strong>: {event}</li>'
        for date, event in data['recent']
    )

    # ── Sources
    src_lines = []
    for src in data['sources']:
        if len(src) == 3:
            name, detail, url = src
            link = f' <a href="{url}" rel="external nofollow">{url.split("//")[-1].rstrip("/")[:40]}{"..." if len(url.split("//")[-1].rstrip("/")) > 40 else ""}</a>'
        else:
            name, detail = src[0], src[1]
            link = ''
        src_lines.append(f'      <li><strong>{name}</strong> — {detail}.{link}</li>')
    # Add OECD source first (universal)
    oecd_src = ('      <li>\n'
                '        <strong>OECD Inclusive Framework</strong> — Updated Central Record for Purposes of the\n'
                '        Global Minimum Tax, 2026-05-11 승인 (2026-05-01 기준).\n'
                '        <a href="https://www.oecd.org/en/topics/policy-sub-issues/global-minimum-tax/" rel="external nofollow">OECD 글로벌최저한세 페이지</a>\n'
                '      </li>')
    sources_html = oecd_src + '\n' + '\n'.join(src_lines)

    # ── Full page
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pillar Two in {name_ko} — {name_en} | PillarTwo Architect</title>
<meta name="description" content="{name_ko}의 Pillar Two(글로벌최저한세) 도입 현황. IIR · UTPR · QDMTT 시행일, 도입 법령, 실무 시사점 정리.">
<meta name="robots" content="index, follow">
<meta name="naver-site-verification" content="03dcd7169d0affc69d6ebf2e0a2af01dd5694073" />
<meta name="naver-site-verification" content="b15c8fd7be4aab298a81448b4c4e346fc613d30a" />
<link rel="canonical" href="https://pillartwo.app/jurisdictions/{slug}">
<link rel="alternate" hreflang="ko" href="https://pillartwo.app/jurisdictions/{slug}?lang=ko">
<link rel="alternate" hreflang="en" href="https://pillartwo.app/jurisdictions/{slug}?lang=en">
<link rel="alternate" hreflang="ja" href="https://pillartwo.app/jurisdictions/{slug}?lang=ja">
<link rel="alternate" hreflang="x-default" href="https://pillartwo.app/jurisdictions/{slug}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "PillarTwo Architect", "item": "https://pillartwo.app/" }},
    {{ "@type": "ListItem", "position": 2, "name": "Jurisdictions", "item": "https://pillartwo.app/jurisdictions/" }},
    {{ "@type": "ListItem", "position": 3, "name": "{name_en}", "item": "https://pillartwo.app/jurisdictions/{slug}" }}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Pillar Two in {name_en} — Adoption Status, Effective Dates, and Implications",
  "description": "Reference on {name_en}'s implementation of OECD Pillar Two (GloBE Rules) — IIR, UTPR, and Qualified Domestic Minimum Top-up Tax (QDMTT) effective dates and qualified status as of 2026-05-28.",
  "image": "https://pillartwo.app/og-image.png",
  "datePublished": "2026-05-28",
  "dateModified": "2026-05-28",
  "author": {{ "@type": "Organization", "name": "PillarTwo Architect" }},
  "publisher": {{ "@type": "Organization", "name": "PillarTwo Architect", "url": "https://pillartwo.app" }},
  "mainEntityOfPage": "https://pillartwo.app/jurisdictions/{slug}",
  "about": [
    {{ "@type": "Country", "name": "{name_en}", "alternateName": ["{name_ko}", "{data['name_ja']}"] }},
    {{ "@type": "Thing", "name": "OECD Pillar Two GloBE Rules" }}
  ],
  "citation": [
    {{ "@type": "CreativeWork", "name": "OECD Updated Central Record for Purposes of the Global Minimum Tax", "datePublished": "2026-05-11", "url": "https://www.oecd.org/en/topics/sub-issues/global-minimum-tax/" }}
  ]
}}
</script>
<meta property="og:type" content="article">
<meta property="og:title" content="Pillar Two in {name_ko} — {name_en}">
<meta property="og:description" content="{name_ko}의 Pillar Two 시행일·도입 법령·실무 시사점.">
<meta property="og:url" content="https://pillartwo.app/jurisdictions/{slug}">
<meta property="og:image" content="https://pillartwo.app/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Pillar Two in {name_ko} — {name_en}">
<meta name="twitter:description" content="{name_ko}의 Pillar Two 시행일·도입 법령·실무 시사점.">
<meta name="twitter:image" content="https://pillartwo.app/og-image.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#2563eb">
{SENTRY_HEAD}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/docs.css">
<link rel="stylesheet" href="/jurisdictions/jurisdictions.css">
</head>
<body class="docs-body">

<nav class="docs-nav">
  <a class="docs-brand" href="/">
    {BRAND_SVG}
    <span class="docs-brand-name">Pillar<em>Two</em></span>
    <span class="docs-brand-sub">Architect</span>
  </a>
  <div class="docs-nav-links">
    <a href="/">← 아키텍트로 돌아가기</a>
    <a href="/overview.html">Pillar Two</a>
    <a href="/jurisdictions/" class="active">국가별 현황</a>
    <a href="/about.html">서비스 소개</a>
  </div>
</nav>

<main class="docs-main">

  <header class="docs-hero">
    <div class="jr-breadcrumb">
      <a href="/jurisdictions/">국가별 현황</a> <span>›</span> {name_ko}
    </div>
    <h1 class="jr-h1">
      <img class="jr-flag-img" src="https://flagcdn.com/w80/{data['flag_cc']}.png" srcset="https://flagcdn.com/w160/{data['flag_cc']}.png 2x" width="40" height="30" alt="{name_ko} 국기" loading="lazy">
      Pillar Two in {name_ko}
    </h1>
    <p class="docs-lead">
      {data['lead']}
    </p>
  </header>

  <section class="docs-section jr-tl-section">
    <h2>시행 타임라인</h2>
    <div class="jr-timeline" role="list" aria-label="{name_ko} Pillar Two 시행 타임라인">
      {tl_html}
    </div>
    <p class="jr-tl-note">위 일자 이후 <strong>개시</strong>하는 사업연도부터 각 규정이 적용됩니다.</p>
  </section>

  <section class="docs-section">
    <h2>Quick reference</h2>
    <table class="jr-quick">
      <thead>
        <tr><th>규정</th><th>시행일</th><th>상태</th></tr>
      </thead>
      <tbody>
{quick_html}
      </tbody>
    </table>
  </section>

  <section class="docs-section">
    <h2>도입 법령</h2>
    <ul class="docs-list jr-laws">
{laws_html}
    </ul>
  </section>

  <section class="docs-section">
    <h2>실무 시사점</h2>
{insights_html}
  </section>

  <section class="docs-section">
    <h2>최근 입법 동향</h2>
    <ul class="docs-list">
{recent_html}
    </ul>
  </section>

  <section class="docs-section">
    <h2>관련 용어</h2>
    <div class="jr-related-terms">
      <a href="/glossary#iir" class="jr-term-chip">소득산입규칙 (IIR)</a>
      <a href="/glossary#utpr" class="jr-term-chip">소득산입보완규칙 (UTPR)</a>
      <a href="/glossary#qdmtt" class="jr-term-chip">적격소재국추가세 (QDMTT)</a>
      <a href="/glossary#qdmttsh" class="jr-term-chip">QDMTT Safe Harbour</a>
      <a href="/glossary#topup" class="jr-term-chip">추가세액 (Top-up Tax)</a>
      <a href="/glossary#etr" class="jr-term-chip">실효세율 (ETR)</a>
      <a href="/glossary#mne" class="jr-term-chip">다국적기업그룹 (MNE Group)</a>
    </div>
  </section>

  <section class="docs-section jr-cta-section">
    <h2>PillarTwo Architect에서 분석해 보기</h2>
    <p>{name_ko} 기업이 포함된 그룹을 아키텍처에 설계하고 글로벌최저한세 청사진을 즉시 확인하세요.</p>
    <a href="/" class="docs-btn primary">분석 시작 →</a>
    <a href="/overview.html" class="docs-btn ghost" data-i18n="docs.nav.overview">Pillar Two</a>
    <a href="/about.html" class="docs-btn ghost" data-i18n="docs.nav.about">서비스 소개</a>
    <a href="/glossary" class="docs-btn ghost" data-i18n="docs.nav.glossary">용어 사전</a>
  </section>

  <section class="docs-section jr-sources">
    <h2>출처</h2>
    <ul class="docs-list">
{sources_html}
    </ul>
  </section>

  <section class="docs-section jr-disclaimer-section">
    <div class="jr-disclaimer">
      <h3>Disclaimer</h3>
      <p>
        본 페이지는 <strong>2026-05-28 기준</strong>으로 위 1차 자료를 종합해 정리한 참조 정보이며,
        법률·세무 자문이 아닙니다. 실무 적용 전에는 반드시:
      </p>
      <ul>
        <li>가장 최신 법령·행정해석·세무 당국 안내를 확인할 것</li>
        <li>자격을 갖춘 세무 전문가의 검토를 받을 것</li>
        <li>그룹의 구체적 사실관계에 비추어 적용 여부를 재판단할 것</li>
      </ul>
      <p class="jr-meta-stamp">
        Last verified: <time datetime="2026-05-28">2026-05-28</time>
        · OECD Central Record dated 1 May 2026 기준
      </p>
    </div>
  </section>

</main>

<footer class="docs-footer">
  <div class="docs-footer-inner">
    <span>© PillarTwo Architect</span>
    <span class="docs-footer-sep">·</span>
    <a href="/">← 아키텍트로 돌아가기</a>
    <span class="docs-footer-sep">·</span>
    <a href="/overview.html">Pillar Two</a>
    <span class="docs-footer-sep">·</span>
    <a href="/glossary">용어 사전</a>
    <span class="docs-footer-sep">·</span>
    <a href="/about.html">서비스 소개</a>
  </div>
</footer>

<div class="docs-lang-toggle">
  <button class="docs-lang-btn" data-lang="en">English</button>
  <button class="docs-lang-btn" data-lang="ko">한국어</button>
  <button class="docs-lang-btn" data-lang="ja">日本語</button>
</div>

<script src="/translations.min.js"></script>
<script>
  (function(){{
    let lang='ko';
    try{{ const saved=localStorage.getItem('p2a.lang'); if(saved==='ko'||saved==='en'||saved==='ja') lang=saved; }}catch(e){{}}
    setLang(lang);
    document.querySelectorAll('.docs-lang-btn').forEach(b=>{{
      b.classList.toggle('active', b.dataset.lang===lang);
      b.addEventListener('click',()=>{{
        setLang(b.dataset.lang);
        try{{ localStorage.setItem('p2a.lang', b.dataset.lang); }}catch(e){{}}
        document.querySelectorAll('.docs-lang-btn').forEach(x=>x.classList.toggle('active', x.dataset.lang===b.dataset.lang));
      }});
    }});
  }})();
</script>

</body>
</html>
'''


# ─────────────────────────────────────────────────────────────────
# Index 페이지 (/jurisdictions/) — 40국 카드 그리드 + 검색·지역 필터
# ─────────────────────────────────────────────────────────────────

REGIONS = {
    'EU': ['AT','BE','CZ','DE','DK','ES','FI','FR','GR','HU','IE','IT','LU','NL','PL','PT','RO','SE','SI'],
    'EFTA': ['CH','LI','NO'],
    'UK': ['GB'],
    'APAC': ['AU','HK','ID','JP','KR','MY','NZ','SG','TH','VN'],
    'Americas': ['BR','CA','US'],
    'ME·Africa': ['AE','QA','ZA'],
    'Other': ['TR'],
}


def cc_to_region(cc):
    for r, ccs in REGIONS.items():
        if cc in ccs:
            return r
    return 'Other'


def short_date(d):
    """YYYY-MM-DD → YYYY.MM 형태"""
    if not d:
        return '—'
    parts = d.split('-')
    return f'{parts[0]}.{parts[1]}'


def render_idx_card(cc, data):
    slug = data['slug']
    name_ko = data['name_ko']
    name_en = data['name_en']
    region = cc_to_region(cc)
    iir = data['iir']
    utpr = data['utpr']
    qdmtt = data['qdmtt']

    # Search keys: 한국어·영어·일본어 + cc + slug
    keys = ' '.join([name_ko, name_en, data['name_ja'], cc, slug]).lower()

    def rule_pill(label, info):
        date = info.get('date')
        if not date:
            return f'<span class="jr-idx-rule jr-idx-rule-none"><span class="jr-idx-rl">{label}</span><span class="jr-idx-rd">미도입</span></span>'
        cls = 'jr-idx-rule-ok' if info.get('qualified') else 'jr-idx-rule-pending'
        return f'<span class="jr-idx-rule {cls}"><span class="jr-idx-rl">{label}</span><span class="jr-idx-rd">{short_date(date)}</span></span>'

    pills = ''.join([
        rule_pill('IIR', iir),
        rule_pill('UTPR', utpr),
        rule_pill('QDMTT', qdmtt),
    ])

    return f'''<a href="/jurisdictions/{slug}" class="jr-idx-card" data-region="{region}" data-keys="{keys}">
        <img class="jr-idx-flag" src="https://flagcdn.com/w80/{data['flag_cc']}.png" srcset="https://flagcdn.com/w160/{data['flag_cc']}.png 2x" alt="{name_ko} 국기" loading="lazy" width="40" height="30">
        <div class="jr-idx-body">
          <div class="jr-idx-name">{name_ko}<span class="jr-idx-name-en">{name_en}</span></div>
          <div class="jr-idx-rules">{pills}</div>
        </div>
      </a>'''


def build_index():
    cards = []
    # 알파벳 순 (cc) — 보기에 안정적
    for cc in sorted(COUNTRIES.keys()):
        cards.append(render_idx_card(cc, COUNTRIES[cc]))
    cards_html = '\n      '.join(cards)

    chips = ''.join([
        '<button class="jr-idx-chip is-active" data-region="all">전체</button>',
        '<button class="jr-idx-chip" data-region="EU">EU</button>',
        '<button class="jr-idx-chip" data-region="EFTA">EFTA</button>',
        '<button class="jr-idx-chip" data-region="UK">영국</button>',
        '<button class="jr-idx-chip" data-region="APAC">APAC</button>',
        '<button class="jr-idx-chip" data-region="Americas">Americas</button>',
        '<button class="jr-idx-chip" data-region="ME·Africa">중동·아프리카</button>',
        '<button class="jr-idx-chip" data-region="Other">기타</button>',
    ])

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>국가별 Pillar Two 도입 현황 — 40개국 | PillarTwo Architect</title>
<meta name="description" content="OECD Pillar Two(글로벌최저한세) 도입국 40개국의 IIR · UTPR · QDMTT 시행일·도입 법령·OECD 적격 상태를 한눈에. 국가별 페이지로 빠르게 이동.">
<meta name="robots" content="index, follow">
<meta name="naver-site-verification" content="03dcd7169d0affc69d6ebf2e0a2af01dd5694073" />
<meta name="naver-site-verification" content="b15c8fd7be4aab298a81448b4c4e346fc613d30a" />
<link rel="canonical" href="https://pillartwo.app/jurisdictions/">
<link rel="alternate" hreflang="ko" href="https://pillartwo.app/jurisdictions/?lang=ko">
<link rel="alternate" hreflang="en" href="https://pillartwo.app/jurisdictions/?lang=en">
<link rel="alternate" hreflang="ja" href="https://pillartwo.app/jurisdictions/?lang=ja">
<link rel="alternate" hreflang="x-default" href="https://pillartwo.app/jurisdictions/">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "PillarTwo Architect", "item": "https://pillartwo.app/" }},
    {{ "@type": "ListItem", "position": 2, "name": "Jurisdictions", "item": "https://pillartwo.app/jurisdictions/" }}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "국가별 Pillar Two 도입 현황 — 40개국",
  "description": "OECD Pillar Two(글로벌최저한세) 도입국 40개국의 IIR·UTPR·QDMTT 시행일·도입 법령·OECD 적격 상태 모음.",
  "url": "https://pillartwo.app/jurisdictions/",
  "inLanguage": ["ko", "en", "ja"],
  "datePublished": "2026-05-28",
  "dateModified": "2026-05-28"
}}
</script>
<meta property="og:type" content="website">
<meta property="og:title" content="국가별 Pillar Two 도입 현황 — 40개국">
<meta property="og:description" content="OECD Pillar Two 도입국 40개국의 IIR · UTPR · QDMTT 시행일·도입 법령·OECD 적격 상태를 한눈에.">
<meta property="og:url" content="https://pillartwo.app/jurisdictions/">
<meta property="og:image" content="https://pillartwo.app/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="국가별 Pillar Two 도입 현황 — 40개국">
<meta name="twitter:description" content="OECD Pillar Two 도입국 40개국의 IIR · UTPR · QDMTT 시행일·도입 법령·OECD 적격 상태를 한눈에.">
<meta name="twitter:image" content="https://pillartwo.app/og-image.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#2563eb">
{SENTRY_HEAD}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/docs.css">
<link rel="stylesheet" href="/jurisdictions/jurisdictions.css">
</head>
<body class="docs-body">

<nav class="docs-nav">
  <a class="docs-brand" href="/">
    {BRAND_SVG}
    <span class="docs-brand-name">Pillar<em>Two</em></span>
    <span class="docs-brand-sub">Architect</span>
  </a>
  <div class="docs-nav-links">
    <a href="/">← 아키텍트로 돌아가기</a>
    <a href="/overview.html">Pillar Two</a>
    <a href="/jurisdictions/" class="active">국가별 현황</a>
    <a href="/about.html">서비스 소개</a>
  </div>
</nav>

<main class="docs-main">

  <header class="docs-hero">
    <h1 class="docs-h1">국가별 Pillar Two 도입 현황</h1>
    <p class="docs-lead">
      OECD Pillar Two(글로벌최저한세) 도입국 <strong>40개국</strong>의 IIR · UTPR · QDMTT 시행일과
      OECD 적격 상태를 한눈에 정리했습니다. 카드를 클릭하면 해당국 상세 페이지로 이동합니다.
    </p>
  </header>

  <section class="docs-section">
    <div class="jr-idx-toolbar">
      <input type="search" id="jr-idx-search" class="jr-idx-search" placeholder="국가명 검색 (한·영·일·국가코드)…" aria-label="국가명 검색">
      <div class="jr-idx-chips">{chips}</div>
    </div>

    <div class="jr-idx-grid" id="jr-idx-grid">
      {cards_html}
    </div>
    <p class="jr-idx-empty" id="jr-idx-empty" style="display:none">일치하는 국가가 없습니다.</p>
  </section>

  <section class="docs-section docs-cta">
    <a href="/" class="docs-btn primary">아키텍트 사용하기 →</a>
    <a href="/overview.html" class="docs-btn ghost" data-i18n="docs.nav.overview">Pillar Two</a>
    <a href="/about.html" class="docs-btn ghost" data-i18n="docs.nav.about">서비스 소개</a>
    <a href="/glossary" class="docs-btn ghost" data-i18n="docs.nav.glossary">용어 사전</a>
  </section>

  <section class="docs-section jr-disclaimer-section">
    <div class="jr-disclaimer">
      <h3>Disclaimer</h3>
      <p>
        본 페이지는 <strong>2026-05-28 기준</strong> OECD Inclusive Framework의 Updated Central Record
        (2026-05-11 승인, 2026-05-01 기준) 및 각국 1차 자료를 종합해 정리한 참조 정보이며, 법률·세무 자문이
        아닙니다. 실무 적용 전에는 반드시 가장 최신 법령·행정해석을 확인하고 자격을 갖춘 세무 전문가의 검토를 받으시기 바랍니다.
      </p>
      <p class="jr-meta-stamp">
        Last verified: <time datetime="2026-05-28">2026-05-28</time>
        · OECD Central Record dated 1 May 2026 기준
      </p>
    </div>
  </section>

</main>

<footer class="docs-footer">
  <div class="docs-footer-inner">
    <span>© PillarTwo Architect</span>
    <span class="docs-footer-sep">·</span>
    <a href="/">← 아키텍트로 돌아가기</a>
    <span class="docs-footer-sep">·</span>
    <a href="/overview.html">Pillar Two</a>
    <span class="docs-footer-sep">·</span>
    <a href="/glossary">용어 사전</a>
    <span class="docs-footer-sep">·</span>
    <a href="/about.html">서비스 소개</a>
  </div>
</footer>

<script>
(function(){{
  const search = document.getElementById('jr-idx-search');
  const chips = document.querySelectorAll('.jr-idx-chip');
  const cards = document.querySelectorAll('.jr-idx-card');
  const empty = document.getElementById('jr-idx-empty');
  let activeRegion = 'all';
  function apply(){{
    const q = (search.value || '').toLowerCase().trim();
    let visible = 0;
    cards.forEach(c => {{
      const matchRegion = activeRegion === 'all' || c.dataset.region === activeRegion;
      const matchQ = !q || (c.dataset.keys || '').includes(q);
      const show = matchRegion && matchQ;
      c.style.display = show ? '' : 'none';
      if (show) visible++;
    }});
    empty.style.display = visible === 0 ? 'block' : 'none';
  }}
  search.addEventListener('input', apply);
  chips.forEach(ch => ch.addEventListener('click', () => {{
    chips.forEach(x => x.classList.toggle('is-active', x === ch));
    activeRegion = ch.dataset.region;
    apply();
  }}));
}})();
</script>

</body>
</html>
'''


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'en').mkdir(exist_ok=True)
    (OUT_DIR / 'ja').mkdir(exist_ok=True)
    args = sys.argv[1:]
    build_idx = (not args) or ('INDEX' in args)
    only = [a for a in args if a in COUNTRIES] if args else list(COUNTRIES.keys())
    for cc in only:
        data = COUNTRIES[cc]
        # 한국어 (수동 작성 4국은 스킵)
        if not data.get('index_only'):
            html = render_page(cc, data)
            path = OUT_DIR / f'{data["slug"]}.html'
            path.write_text(html, encoding='utf-8')
            print(f'wrote {path.relative_to(ROOT)} ({len(html)} chars)')
        # English (수동 작성 4국 중 KR은 별도 manual, 나머지 JP/US/GB는 데이터 부족 시 skip)
        if not data.get('skip_intl'):
            for lang in ('en', 'ja'):
                html = render_page_intl(cc, data, lang)
                path = OUT_DIR / lang / f'{data["slug"]}.html'
                path.write_text(html, encoding='utf-8')
                print(f'wrote {path.relative_to(ROOT)} ({len(html)} chars)')
    if build_idx:
        idx_html = build_index()
        idx_path = OUT_DIR / 'index.html'
        idx_path.write_text(idx_html, encoding='utf-8')
        print(f'wrote {idx_path.relative_to(ROOT)} ({len(idx_html)} chars)')


if __name__ == '__main__':
    main()
