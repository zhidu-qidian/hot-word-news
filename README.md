
# 抓取热词及热点新闻标题


**注意**：

+ 该脚本依赖PG后台那边的`/v2/hot/crawler/news`上报接口
+ 在`db.py`中配置mongo数据库IP\PORT\鉴权信息

***热词新闻***

+ 网易新闻1小时榜 http://news.163.com/rank/
+ 新浪总榜 http://news.sina.com.cn/hotnews/
+ 凤凰点击榜 http://news.ifeng.com/hotnews/

***热词***
 
+ 百度热词：http://news.baidu.com/n?cmd=1&class=reci



### 运行
```bash
python hot_word_news.py
```