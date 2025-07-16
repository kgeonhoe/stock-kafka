#!/usr/bin/env python3
"""
폴더 구조 요약 도구 (Folder Structure Summary Tool)
Korean Investment Securities Kafka Pipeline 프로젝트용

현재 디렉토리의 폴더 구조를 트리 형태로 요약하여 보여줍니다.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class FolderStructureSummary:
    """폴더 구조 요약 생성기"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            '.venv', '.env', 'venv', '.mypy_cache', '.tox',
            '*.pyc', '*.pyo', '*.pyd', '.DS_Store', 'Thumbs.db',
            '.coverage', '.cache', 'dist', 'build', 'egg-info',
            '.idea', '.vscode', '.vs'
        }
        
        # 한국어 디렉토리 설명
        self.directory_descriptions = {
            'src': '🏗️ 소스 코드 - 메인 애플리케이션 로직',
            'src/processors': '⚙️ 데이터 처리기 - 배치 및 실시간 처리',
            'src/api': '🔌 API 클라이언트 - 외부 서비스 연동',
            'config': '⚙️ 설정 파일 - 시스템 구성',
            'data': '📊 데이터 저장소 - 데이터베이스 및 캐시',
            'data/duckdb': '🦆 DuckDB 데이터베이스 파일',
            'scripts': '📝 스크립트 - 유틸리티 및 설정',
            'docs': '📚 문서 - 프로젝트 문서화',
            'tests': '🧪 테스트 - 단위 및 통합 테스트',
            '.': '📁 프로젝트 루트 디렉토리'
        }
        
        # 파일 타입별 설명
        self.file_descriptions = {
            'requirements.txt': '📦 Python 의존성 패키지 목록',
            'pyproject.toml': '🔧 Python 프로젝트 설정 파일',
            'docker-compose.yml': '🐳 Docker 컨테이너 설정',
            'Dockerfile': '🐳 Docker 이미지 빌드 설정',
            'README.md': '📖 프로젝트 소개 및 사용법',
            'PROJECT_ARCHITECTURE.md': '🏗️ 프로젝트 아키텍처 문서',
            '.gitignore': '🚫 Git 무시 파일 목록',
            'uv.lock': '🔒 의존성 락 파일',
            'run.sh': '🚀 실행 스크립트',
            '.env.example': '🔒 환경 변수 예시 파일'
        }
    
    def should_ignore(self, path: Path) -> bool:
        """무시할 파일/폴더인지 확인"""
        name = path.name
        
        # 숨김 파일/폴더 (일부 예외 제외)
        if name.startswith('.') and name not in {'.env.example', '.gitignore', '.python-version'}:
            return True
            
        # 무시 패턴 확인
        for pattern in self.ignore_patterns:
            if pattern in name or name == pattern:
                return True
                
        return False
    
    def get_file_info(self, path: Path) -> Dict:
        """파일 정보 수집"""
        try:
            stat = path.stat()
            return {
                'name': path.name,
                'size': stat.st_size,
                'is_dir': path.is_dir(),
                'description': self.file_descriptions.get(path.name, '')
            }
        except (OSError, PermissionError):
            return {
                'name': path.name,
                'size': 0,
                'is_dir': path.is_dir(),
                'description': ''
            }
    
    def scan_directory(self, path: Path, max_depth: int = 3, current_depth: int = 0) -> Dict:
        """디렉토리를 재귀적으로 스캔"""
        if current_depth > max_depth:
            return {}
        
        result = {
            'name': path.name if path != self.root_path else self.root_path.name,
            'path': str(path.relative_to(self.root_path)),
            'is_dir': True,
            'description': self.directory_descriptions.get(str(path.relative_to(self.root_path)), ''),
            'children': []
        }
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if self.should_ignore(item):
                    continue
                
                if item.is_dir():
                    child = self.scan_directory(item, max_depth, current_depth + 1)
                    if child:
                        result['children'].append(child)
                else:
                    file_info = self.get_file_info(item)
                    file_info['path'] = str(item.relative_to(self.root_path))
                    result['children'].append(file_info)
        
        except (OSError, PermissionError):
            pass
        
        return result
    
    def format_tree(self, tree: Dict, prefix: str = "", is_last: bool = True) -> List[str]:
        """트리 구조를 문자열로 포맷팅"""
        lines = []
        
        # 현재 아이템 출력
        connector = "└── " if is_last else "├── "
        name_with_desc = tree['name']
        
        if tree.get('description'):
            name_with_desc += f" - {tree['description']}"
        
        lines.append(f"{prefix}{connector}{name_with_desc}")
        
        # 자식 아이템들 처리
        children = tree.get('children', [])
        if children:
            extension = "    " if is_last else "│   "
            new_prefix = prefix + extension
            
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                lines.extend(self.format_tree(child, new_prefix, is_last_child))
        
        return lines
    
    def generate_summary(self, max_depth: int = 3) -> str:
        """폴더 구조 요약 생성"""
        tree = self.scan_directory(self.root_path, max_depth)
        
        header = f"""
📁 Stock Kafka Pipeline - 폴더 구조 요약
{'=' * 50}
프로젝트 경로: {self.root_path}
최대 탐색 깊이: {max_depth}
생성 시간: {os.popen('date').read().strip()}

🗂️ 디렉토리 구조:
"""
        
        tree_lines = self.format_tree(tree)
        
        footer = f"""
{'=' * 50}
📊 요약 통계:
- 총 탐색된 아이템: {self._count_items(tree)}
- 디렉토리 수: {self._count_directories(tree)}
- 파일 수: {self._count_files(tree)}

💡 사용법:
  python src/folder_structure_summary.py --max-depth 2
  python src/folder_structure_summary.py --path /다른/경로
"""
        
        return header + '\n'.join(tree_lines) + footer
    
    def _count_items(self, tree: Dict) -> int:
        """총 아이템 수 계산"""
        count = 1
        for child in tree.get('children', []):
            count += self._count_items(child)
        return count
    
    def _count_directories(self, tree: Dict) -> int:
        """디렉토리 수 계산"""
        count = 1 if tree.get('is_dir', False) else 0
        for child in tree.get('children', []):
            count += self._count_directories(child)
        return count
    
    def _count_files(self, tree: Dict) -> int:
        """파일 수 계산"""
        count = 0 if tree.get('is_dir', False) else 1
        for child in tree.get('children', []):
            count += self._count_files(child)
        return count


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='프로젝트 폴더 구조를 요약하여 보여줍니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--path', '-p',
        default='.',
        help='탐색할 디렉토리 경로 (기본값: 현재 디렉토리)'
    )
    
    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        default=3,
        help='최대 탐색 깊이 (기본값: 3)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='결과를 파일로 저장할 경로 (선택사항)'
    )
    
    args = parser.parse_args()
    
    try:
        # 폴더 구조 요약 생성
        summary = FolderStructureSummary(args.path)
        result = summary.generate_summary(args.max_depth)
        
        # 결과 출력
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ 폴더 구조 요약이 {args.output}에 저장되었습니다.")
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())