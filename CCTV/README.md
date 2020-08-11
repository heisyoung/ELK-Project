# ELK를 활용한 CCTV 탐지 로그 관리 시스템
사용된 프로그래밍 언어는 파이썬이며, 프로그램 동작 순서는 다음과 같습니다.
1. cctv.py는 CCTV 프로그램이며 실행 후 탐지 로그를 남기면 Filebeat를 통해 Logstash로 로그를 전달합니다.
2. Logstash로 전달된 로그는 구문 분석을 통해 Elastic Search에 저장됩니다.
3. alert.py는 cctv.py의 로그가 ES에 저장되면 관리자에게 알림창을 보내는 프로그램이며, 탐지 원인에 대한 수정도 가능합니다.
4. 관리자는 Kibana Dashboard에 시작화된 로그 데이터를 보면서 모니터링이 가능합니다.