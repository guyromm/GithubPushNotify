import re,json,dateutil
import MySQLdb as my
args = json.loads(open('mysql.json','r').read())
conn = my.connect(**args)

storyre = re.compile('#(\d+)')
nomatch={}
#sql to see there are no dupes by message:
#-- select * from (select comment,object_id,count(*) cnt from threadedcomments_threadedcomment where comment like 'github commit%' group by comment,object_id order by cnt) foo where cnt>1;
#sql to see/delete existing github commit comments:
#-- select * from threadedcomments_threadedcomment where comment like 'github commit%'\G
def import_commit(repo,payload):
    global nomatch
    if 'payload' in payload:
        loopover = payload['payload']
    else:
        loopover = payload
    for commit in loopover['commits']:
        sres = storyre.search(commit['message'])
        fstoryid=None
        if sres:
            storyid = sres.group(1)
            c = conn.cursor()
            res = c.execute("select id from projects_story where id=%s or local_id=%s",(storyid,storyid))
            row = c.fetchone()
            if row:
                fstoryid = row[0]
                print 'found story id by direct method'
            else:
                #try to look by tag
                c.execute("select id from projects_storytag where name=%s","pivotal id %s"%storyid)
                res = c.fetchone()
                if res: 
                    tagid = res[0]
                    c.execute("select story_id from projects_storytagging where tag_id=%s",tagid)
                    res = c.fetchone()
                    if res:
                        fstoryid = res[0]
                        print 'found story %s by looking for pivotal tag %s'%(fstoryid,storyid)
            if fstoryid:
                print('want to tie this commit\'s story %s -> %s'%(storyid,fstoryid))
                userid=1
                import iso8601
                print 'trying to parse %s'%commit['timestamp']
                pdate = iso8601.parse_date(commit['timestamp']) #dateutil.parser.parse(commit['timestamp'])
                comurl = commit['url'] #comid = '/%s/%s/commit/%s'%(GITHUB_USER,projfn,c['id'])
                message = 'github commit %s :\n %s'%(comurl,commit['message'])
                c.execute("select count(*) from threadedcomments_threadedcomment where user_id=%s and object_id=%s and comment=%s",(userid,fstoryid,message))
                excom = c.fetchone()[0]
                if not excom:
                    cres = c.execute("""insert into threadedcomments_threadedcomment (
                    content_type_id
                    ,object_id
                        ,user_id
                        ,date_submitted
                        ,comment
                        ,markup
                        ,is_public,is_approved,date_modified
                       ) values(
                        35 -- content type id
                        ,%s
                        ,%s -- user
                        ,%s -- date submitted
                        ,%s -- comment
                        ,5 -- markup
                        ,1 -- is public
                        ,0 -- is approved
                        ,%s
                        )""",(fstoryid,userid,pdate,message,pdate))
                    assert cres
                    print 'inserted commit comment %s -> %s'%(message,fstoryid)
                else:
                    print 'comment already exists.'
            else:
                if storyid not in nomatch:
                    nomatch[storyid]=0
                nomatch[storyid]+=1
                print 'story %s from message "%s" does not match any scrumdo story'%(storyid,commit['message'])
    #print nomatch
