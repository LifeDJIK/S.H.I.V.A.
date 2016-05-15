# S.H.I.V.A.
S.H.I.V.A. - Social network History &amp; Information Vault &amp; Analyser

# Deployment
* docker-compose up -d
* docker exec `docker-compose ps mongo1 | tail -n 1 | cut -d' ' -f1` mongo --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host: "mongo1"},{_id:1,host:"mongo2"},{_id:2,host:"mongo3"}]})'
* docker-compose run --rm shiva1 python /usr/src/app/tools/add_user.py test test 0
