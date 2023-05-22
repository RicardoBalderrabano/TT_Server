class DevelopmentConfig():
    DEBUG=True
    MYSQL_HOST='140.84.179.17'
    MYSQL_USER='admin'
    MYSQL_PASSWORD='crCY$!55C6_a35D?'
    MYSQL_DB='ROSTROS'
    UPLOAD_FOLDER='/home/ubuntu/tmp'

class ProductionConfig():
    DEBUG=False
    MYSQL_HOST='localhost'
    MYSQL_USER='admin'
    MYSQL_PASSWORD='crCY$!55C6_a35D?'
    MYSQL_DB='ROSTROS'
    UPLOAD_FOLDER='/home/ubuntu/tmp'

config={
    'development':DevelopmentConfig,
    'production':ProductionConfig
}
