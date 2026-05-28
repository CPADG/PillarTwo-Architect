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
            ('APAC 금융 hub 특성', '홍콩은 APAC 지역의 금융·홀딩 기능이 집중된 관할권으로, Pillar Two 분석 시 홍콩 영역원천주의 세제와의 상호작용을 별도로 검토할 필요가 있습니다.'),
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
            ('Tech·Pharma 헤드쿼터 hub 특성', '아일랜드는 글로벌 IT·제약 기업의 본부·IP 보유 기능이 집중된 관할권입니다. Pillar Two 분석 시 아일랜드의 R&D 세액공제, IP regime 등과의 상호작용을 별도로 검토할 필요가 있습니다.'),
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
            ('EU 지주회사 hub 특성', '룩셈부르크는 EU 지주회사·투자펀드·증권화 vehicle 등의 hub로 활용되는 관할권입니다. Pillar Two 분석 시 SOPARFI·SICAR·SICAV 등 vehicle 유형별 적용 가능성과 함께 룩셈부르크의 IP regime 등과의 상호작용을 별도로 검토할 필요가 있습니다.'),
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
            ('헤드쿼터·금융 hub 특성', '스위스는 글로벌 본부·금융·연구 기능이 집중된 관할권으로, 칸톤(주)별로 차등화된 법인세율과 특별 인센티브 영향으로 자회사 ETR이 임계치 하회하는 사례가 발생할 수 있습니다.'),
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
    <a href="/glossary" class="docs-btn ghost">용어 사전</a>
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


def main():
    OUT_DIR.mkdir(exist_ok=True)
    only = sys.argv[1:] if len(sys.argv) > 1 else list(COUNTRIES.keys())
    for cc in only:
        if cc not in COUNTRIES:
            print(f'skip {cc} — not in data')
            continue
        data = COUNTRIES[cc]
        html = render_page(cc, data)
        path = OUT_DIR / f'{data["slug"]}.html'
        path.write_text(html, encoding='utf-8')
        print(f'wrote {path.relative_to(ROOT)} ({len(html)} chars)')


if __name__ == '__main__':
    main()
