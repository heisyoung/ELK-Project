# ELK 세팅
프로젝트에 사용된 버전은 7.8이며, 도커 컴포즈를 사용하여 구축했다.
#### Elastic Search
1. X-Pack trial 30일 사용
2. 아이디, 패스워드 초기값 그대로 설정
#### Logstash
1. pipline/logstash.conf 파일을 수정한다.

```
input {
	beats {
	port => 5000
	}
}

filter {
	dissect {
		mapping => { "message" => "%{location} %{lat} %{lon} %{detect_motion} %{object}" }
	        remove_field => [ "host", "@version", "path", "message" ]
	    }
	mutate {
        	add_field => { "[location-geopoint][lat]" => "%{lat}" }
        	add_field => { "[location-geopoint][lon]" => "%{lon}" }
        }
        mutate {
        	convert => {"[location-geopoint][lat]" => "float"}
        	convert => {"[location-geopoint][lon]" => "float"}
        }
}
output {
	elasticsearch {
		hosts => ["localhost:9200"]
		index => "cctv"
	}
        stdout {
            codec => rubydebug { }
        }
}
```
> - input : 파일비트로 로그파일을 불러온다.
> - filter : 로그파일의 내용을 공백으로 구분하여 추출 및 매핑하며, 필요없는 필드는 삭제한다. 위치정보는 새롭게 필드를 추가하고, float 타입으로 변환한다.
> - output : ES의 IP/PORT 정보와 인덱스를 설정한다. stdout은 디버그용
#### Kibana
1. Dev tools를 사용하여 인덱스 템플릿을 생성한다.

```
PUT _index_template/template_1
{
	"index_patterns": ["cctv*"],
	"template": {
            "settings": {
                "number_of_shards": 1
            },
            "mappings": {
                "_source": {
                    "enabled": true
                    },
                "properties": {
                    "location-geopoint": {
                        "type": "geo_point"
                    }
            }
	}
}
```
> - 매핑을 안해주면 위치정보가 텍스트 타입으로 지정된다.
#### Filebeat
1. filebeat.yml 파일을 수정한다.
2. 수정 후 filebeat.exe -c .\filebeat.yml -e -v 명령어로 파일비트 실행한다.(윈도우 기준)

```
filebeat.inputs:

- type: log
enabled: true
paths:
- C:/로그 파일 경로(윈도우인 경우 경로 구분은 '\'가 아닌 '/' 으로 해야한다)
tail_files: true 
    
'''

#output.elasticsearch ES부분은 전부 주석처리 한다.
    
'''

output.logstash 로그스태시 부분에는 주석처리를 해제하고 로그스태시의 정보를 입력한다.
    
'''

processors:
- drop_fields:
fields: ["agent.ephemeral_id","agent.hostname","agent.id","agent.name","agent.type","agent.version","ecs.version","input.type","log.file.path","tags","log.offset"]
drop_fields로 필요없는 필드를 모두 제거한다.
'''
> - 파이썬 프로그램이 윈도우로 실행되고 로그를 남기기 때문에 파일비트는 윈도우 버전으로 사용했다.
