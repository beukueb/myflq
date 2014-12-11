#!/bin/env python3

## Implementing a database for STR's [and SNP's]

# #Bash commands to make user and database:
# mysql -uroot -p
# mysql> CREATE USER 'profiler'@'localhost' IDENTIFIED BY 'many#1profile';
# mysql> CREATE DATABASE strdb;
# mysql> GRANT ALL ON strdb.* TO 'profiler'@'localhost';
# 

# #Example code block
# #Starting up
# import MySQLdb
# conn = MySQLdb.connect (host = "localhost",
#                            user = "profiler",
#                            passwd = "many#1profile",
#                            db = "strdb")
# sql = conn.cursor () #Using conn.cursor(MySQLdb.cursors.DictCursor) you can access the results like a dictionary instead of a tuple
# 
# #Creating table and inserting values
# #sql.execute ("DROP TABLE IF EXISTS locus")
# sql.execute ("""
#        CREATE TABLE locus
#        (
#          name     CHAR(40),
#          category CHAR(40)
#        )
#      """)
# sql.execute ("""
#        INSERT INTO locus (name, category)
#        VALUES
#          ('D13S317', 'STR'),
#          ('vWA', 'STR'),
#          ('Amelogenin', 'X-marker'),
#          ('FGA', 'STR')
#      """)
# print("Number of rows inserted: %d" % sql.rowcount)
# 
# #Query table
# sql.execute ("SELECT name, category FROM locus")
# #rows=sql.fetchall() #Easier to use => without 'while 1' loop
# while True:
#     row = sql.fetchone()
#     if row == None: break
#     print("%s, %s" % (row[0], row[1]))
# print("Number of rows returned: %d" % sql.rowcount)
# 
# #Update table
# sql.execute ("""
#          UPDATE locus SET name = 'D8'
#          WHERE name = 'D13S317'
#        """)
# #or#
# sql.execute ("""
#          UPDATE locus SET name = %s
#          WHERE name = %s
#        """, ("D8", "D13S317"))
# #NULL values can be passed to MySQL by either proving a string 'NULL' or None, e.g.:
# sql.execute ("""
#          UPDATE locus SET name = %s
#          WHERE name = %s
#        """, ('NULL', None)) #Would make a line with two MySQL NULL values
#        #However for select statements None doesn't work and you need to use 'NULL'
# 
# #2 equivalent complex select statements
# sql.execute("""SELECT forwardP,reverseP,seqID,alleleValidation FROM BASEtech 
#                             JOIN BASElocustrack USING (techID) 
#                             JOIN BASEstat USING (entryID) 
#                             WHERE locusName = %s AND BASEstat.validated = 0""", (name))
# ##Equivalent to##
# sql.execute("""SELECT forwardP,reverseP,seqID FROM BASEtech 
#                 JOIN BASElocustrack ON BASEtech.techID=BASElocustrack.techID 
#                     JOIN BASEstat ON BASElocustrack.entryID = BASEstat.entryID 
#                     WHERE locusName = %s AND BASEstat.validated = 0""", (name))
# 
# #Closing up
# sql.execute ("DROP TABLE locus")#Because it's just a test run and we don't need this table
# sql.close ()
# conn.commit() #To commit all changes to the database, otherwise changes could be lost, though probably not necessary for MySQL
# conn.close()
# 

# In[1]:

#Future imports for python2.6
from __future__ import print_function
from __future__ import unicode_literals
import sys
python2 = sys.version < '3'
if python2:
    str = unicode
    from itertools import izip as zip
    input = raw_input

#Database functions
def login(user="""admin""",passwd="""passall""",database='MyFLqADMIN', test=False):
    """
    Returns the formed connection with the db using variablenames: conn, sql
    If test: just tests the connection, and closes it again returning None. 
        An exception should be raised automatically if there's a problem with the connection.
    """
    try: import pymysql as MySQLdb
    except ImportError: import MySQLdb #py2#
    conn = MySQLdb.connect(host = "localhost",
                           user = user,
                           passwd = passwd,
                           db = database)
    sql = conn.cursor(MySQLdb.cursors.DictCursor)
    if not test: return (conn,sql)
    else: logout(conn, sql)
#login.database="strdb" #database can be changed, by changing function variable
#in use: strdb (for illumina);iontorrent;roche454

def logout(conn,sql):
    """
    Logout from the database connection
    """
    sql.close()
    conn.commit()
    conn.close()

def dbBackup(backupfile='strdb.sql',restore=True,flush=False):
    """
    Backup database
    If flush == 'onlyFlush', no backup is made, but all the tables are emptied.
    """
    import os
    if flush != 'onlyFlush':
        if python2: input = raw_input
        if not backupfile.startswith('/'): backupfile='mysql/'+backupfile
        if restore: os.system('mysql -uroot -p'+input('Password: ')+' strdb < '+backupfile)
        else: os.system('mysqldump -uroot -p'+input('Password: ')+' strdb > '+backupfile)
    if flush:
        conn,sql=login()
        sql.execute('''TRUNCATE BASElocustrack; TRUNCATE BASEseqs; TRUNCATE BASEstat; 
                        TRUNCATE BASEtech; TRUNCATE LOCIalleles; TRUNCATE LOCIalleles_CE; 
                        TRUNCATE LOCIconflicts; TRUNCATE LOCIkits; TRUNCATE LOCInames; ''')
        logout(conn,sql)


# In[2]:

#To rebuild all tables, drop them all -- Use with care
def dropTables(sql):
    tables = ('BASEseqs','BASEnames','BASEprimersets','BASEqual','BASEtrack','BASEstat','laboratories',
              'LOCInames','LOCIalleles','LOCIalleles','LOCIalleles_CE','LOCIconflicts')
    for table in tables: sql.execute ("DROP TABLE "+table)


# In[3]:

#Create tables
def makeTables(sql):
    #Tables for basic sequence input
        #When a sequence gets added at the very least BASEstat and BASEtrack will have to be updated
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEseqs (
    `seqID` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `sequence` TEXT(1000) NOT NULL COMMENT 'sequence of allele, error sequence or primer'
    )
    COMMENT 'All non processed sequences are maintained here and referenced by seqID in the other tables';
         """)    
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEnames (
    `locusName` CHAR(40) NOT NULL PRIMARY KEY COMMENT  'the name of the locus: mandatory',
    `locusType` INT NULL COMMENT 'indicates repeatsize if STR locus, 0 indicates SNP locus, NULL unknown locusType'
    )
    COMMENT 'table with loci names that are used in the database';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEprimersets (
    `primersetID` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `locusName` CHAR(40) NOT NULL COMMENT  'this is the reference to table BASEnames',
    `forwardP` INT NOT NULL COMMENT  'forward primer id from BASEseqs',
    `reverseP` INT NOT NULL COMMENT  'reverse primer id from BASEseqs',
    
    FOREIGN KEY (`locusName`) REFERENCES BASEnames (`locusName`) ON DELETE CASCADE,
    FOREIGN KEY (`forwardP`) REFERENCES BASEseqs (`seqID`),
    FOREIGN KEY (`reverseP`) REFERENCES BASEseqs (`seqID`)    
    )
    COMMENT 'table with all the primersets in use per locus';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEqual (
    `qualID` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `technology` CHAR(40) COMMENT 'technology used, e.g. Illumina',
    `filterLevel` DOUBLE (5,4) 
        COMMENT  'level under which (error) sequences are not reported, format: 0.x, e.g. 0.01 (=1%)'
    )
    COMMENT 'table with information how sequences were retrieved';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS laboratories (
    `labID` CHAR(40) NOT NULL UNIQUE KEY COMMENT  'identification of the submitting laboratory',
    `passphrase` CHAR(200) NOT NULL COMMENT  'a passphrase or link to a key containing file'
    )
    COMMENT 'Laboratories submitting to current database - for quality control';
    INSERT INTO laboratories (labID,passphrase) VALUES ("NA","NA");
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEtrack (
    `entryID` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `locusName` CHAR(40) NOT NULL, FOREIGN KEY (`locusName`) REFERENCES BASEnames (`locusName`),
    `qualID` INT NOT NULL COMMENT  'this is the reference to table BASEqual',
        FOREIGN KEY (`qualID`) REFERENCES BASEqual (`qualID`) ON DELETE CASCADE,
    `labID` CHAR(40) NOT NULL COMMENT  'identification of the submitting laboratory',
        FOREIGN KEY (`labID`) REFERENCES laboratories (`labID`) ON DELETE CASCADE,
    `validated` BOOLEAN NOT NULL DEFAULT '0' COMMENT  'indicate if at least one allele is validated',
    `manualRevision` BOOLEAN NOT NULL DEFAULT '0' COMMENT  'indicate if validation info was revised manually',
    `nrSeqs` INT NOT NULL COMMENT  'number of sequences submitted',
    `nrReads` INT NOT NULL COMMENT  'total number of reads represented by the submitted sequences',
    `population` CHAR(100) DEFAULT 'NA' COMMENT  'generic origin of sample, usefull for calculating biases',
    `entryTime` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    COMMENT 'tracks each submission of sequences to the database';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS BASEstat (
    `entryID` INT NOT NULL COMMENT  'this is the reference to the BASEtrack table',
        FOREIGN KEY (`entryID`) REFERENCES BASEtrack (`entryID`) ON DELETE CASCADE,
    `seqID` INT NOT NULL COMMENT  'this is the reference to the sequence in table BASEseqs',
        FOREIGN KEY (`seqID`) REFERENCES BASEseqs (`seqID`) ON DELETE CASCADE,
    `primersetID` INT NULL COMMENT 'if available primers with which seq was sequenced',
        FOREIGN KEY (`primersetID`) REFERENCES BASEprimersets (`primersetID`),
    `validated` INT DEFAULT '-1'
        COMMENT '-1 if not validated, 0 if valid. allele, > 0 if valid. error seq. In last case int is reference seqID',
    `alleleValidation` CHAR(10)
        COMMENT 'e.g. for STR: "10.1" or "10.1:4" => allele nr 10.1, :4 => repeat size 4; e.g. SNP "SNP:allele info"',
    `seqCount` BIGINT NOT NULL COMMENT 'number of reads with this sequence'
    )
    COMMENT 'stats on each submitted sequence';
         """)
    
    #Tables for processing loci and profiles
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS LOCInames (
    `locusName` CHAR(40) NOT NULL UNIQUE KEY COMMENT 'identification of the locus',
    `locusType` INT NOT NULL DEFAULT '0' COMMENT  'indicates repeatsize if STR locus, otherwise 0',
    `refseq` TEXT(1000) NOT NULL COMMENT 'reference sequence for the locus, should include the biggest primer spread',
    `ref_forwardP` CHAR(40) COMMENT  'reference forward primer, as little upstream as found',
    `ref_reverseP` CHAR(40) COMMENT  'reference reverse primer, as little downstream as found',
    `flank_forwardP` TEXT(1000) COMMENT  'forward flanking for allele determination (without primer seq)',
    `flank_reverseP` TEXT(1000) COMMENT  'reverse flanking for allele determination (without primer seq)',
    `ref_length` INT COMMENT  'length based on the flanking sequences, not including them',
    `ref_alleleNumber` CHAR(10) 
        COMMENT  'If STR locusType, allele number of the reference sequence: e.g. 4.1 = 4 repeats, one extra base'
    )
    COMMENT 'this table is used directly for the analysis of unknown samples';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS LOCIkits (
    `kitName` CHAR(40) NOT NULL COMMENT 'name of the sequencing kit',
    `locusName` CHAR(40) NOT NULL COMMENT 'identification for a participating locus from table LOCInames',
    UNIQUE (kitName,locusName)
    )
    COMMENT 'kits that can be used for analysis of unknown samples';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS LOCIalleles (
    `locusName` CHAR(40) NOT NULL COMMENT 'identification of the locus in table LOCInames',
    `alleleNumber` DOUBLE (4,1) COMMENT 'a number is not required for non STRs like amelogenine',
    `alleleNomen` CHAR(100) COMMENT 'allele nomenclature entry',
    `alleleSeq` TEXT(1000) NOT NULL COMMENT 'allele sequence for the locus, between the flanking seqs',
    `freqOK` BOOLEAN NOT NULL DEFAULT '0' 
        COMMENT  'boolean to state if allele population is significant for calculating profile probability',
    `popFrequency` FLOAT COMMENT  'population frequency of the allele if significant'
    )
    COMMENT 'all the alleles that were used for determining flanks';
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS LOCIalleles_CE (
    `locusName` CHAR(40) NOT NULL COMMENT 'identification of the locus in table LOCInames',
    `alleleNumber` DOUBLE (4,1) COMMENT 'a number is not required for non STRs like amelogenine',
    `alleleNomen` CHAR(100) COMMENT 'allele nomenclature entry',
    `popFrequency` FLOAT NOT NULL COMMENT  'capillary electrophoresis population frequency of the allele',
    UNIQUE (locusName,alleleNumber)
    );
         """)
    sql.execute ("""
    CREATE TABLE IF NOT EXISTS LOCIconflicts (
    `locusName` CHAR(40) NOT NULL 
        COMMENT 'identification of a locus with conflicting validation info in table LOCInames',
    `validConflict` CHAR(40) NOT NULL COMMENT 'nature of the validation conflict'
    );
         """)


# In[4]:

#Create views and functions
#sql.execute('DROP VIEW BASEcombined;')
def makeViews(sql):
    sql.execute ("""
    CREATE VIEW BASEcombined AS SELECT BASEnames.locusName,forwardP,reverseP,seqID,alleleValidation FROM BASEnames 
                                JOIN BASEtrack USING (locusName) 
                                JOIN BASEstat USING (entryID)
                                JOIN BASEprimersets USING (primersetID);
         """)

def makeFunctions(sql):
    sql.execute("""
                CREATE FUNCTION getSeq (primer INT)
                RETURNS TEXT(1000) DETERMINISTIC
                RETURN (SELECT sequence FROM BASEseqs WHERE seqID = primer);
                """)
    #READS SQL DATA


# In[5]:

def setUpUserDatabase(user,password):
    """
    Set up MyFLqADMIN databases.
    This would allow in the future for users to share their databases.
    However, currently not yet implemented.
    """
#This section needs to be elaborated for implementing extra features
    conn,sql = login(user=user,passwd=password,database=None)
    sql.execute("""
    CREATE DATABASE MyFLqADMIN;
    USE MyFLqADMIN;
    """)
#    CREATE TABLE users (
#        `userID` CHAR(40) NOT NULL UNIQUE KEY COMMENT  'identification of the user',
#        `passphrase` CHAR(200) NOT NULL COMMENT  'a passphrase or link to a key containing file'
#    );
#    CREATE TABLE dbases (
#        `database` CHAR(40) NOT NULL UNIQUE KEY COMMENT  'database => currently only one user can own database',
#        `userID` CHAR(40) NOT NULL COMMENT  'identification of the user => table users'
#    );
#    """)
    logout(conn,sql)
    
    #Rewrite scriptfile with MySQL admin credentials
    import sys
    scriptfile = sys.argv[0]
    scriptlines = open(scriptfile).readlines()
    for l in range(len(scriptlines)):
        if scriptlines[l].startswith('def login(user='): break
    scriptlines[l] = 'def login(user="""'+user+'""",passwd="""'+password+'""",database=\'MyFLqADMIN\', test=False):\n'
    scriptfile = open(scriptfile,'wt')
    scriptfile.writelines(scriptlines)
    scriptfile.close()


# In[ ]:

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Add a user, or database for the MyFLq application')
    parser.add_argument('user', help='User for which a database will be created')
    parser.add_argument('db',nargs='*',help='Database[s] to create')
    parser.add_argument('-p','--password',help='MySQL user password (if not provided, will be asked for)')
    parser.add_argument('--delete', action="store_true",help='Delete database[s] instead')
    parser.add_argument('--delete-user', action="store_true",help='Delete user instead')
    parser.add_argument('--install', action="store_true", 
                        help='''Sets up the system to add users and databases for MyFLq
                        MySQL admin 'user' with the ability to create users, databases, functions and assign rights
                        has to be provided on the commandline.
                        The user and password will be recorded in the scriptfile itself.
                        ''')
    args = parser.parse_args()
    if not args.password:
        import getpass
        try: args.password = getpass.getpass('MySQL password for '+args.user+': ')
        except EOFError: args.password = input('MySQL password for '+args.user+': ')
    if args.install: setUpUserDatabase(args.user,args.password)
    else:
        #Check if user and password match => if user is authorised to make or change MyFLq databases
        conn,sql = login()
        sql.execute("""
        SELECT User FROM mysql.user WHERE User = %s;
        """,args.user)
            #SELECT passphrase FROM users WHERE %s = userID; #when using MyFLqADMIN
        if not sql.rowcount:
            sql.execute("CREATE USER %s@'localhost' IDENTIFIED BY %s;",(args.user,args.password))
                #Comments for future implementation
            #sql.execute("INSERT INTO users (userID,passphrase) VALUES (%s,%s)",(args.user,args.password))
            #sql.execute("GRANT SELECT ON MyFLqADMIN.dbases TO %s@'localhost';",args.user)
        #else:
        #    if sql.fetchone()['passphrase'] != args.password:
        #        raise Exception('Password provided does not match user password')
        if not (args.delete or args.delete_user):
            for db in args.db:
                sql.execute("CREATE DATABASE "+db+";")
                sql.execute("GRANT ALL ON "+db+".* TO %s@'localhost';",args.user)
                #sql.execute("INSERT INTO dbases (dbases.database,userID) VALUES (%s,%s)",(db,args.user))
                    #above line would be to allow users sharing dbases, but not implemented yet
                    #could also be implemented from a meta application like MyFLsite
            
            #Make tables
            for db in args.db:
                sql.execute("USE "+db+";")
                makeTables(sql)
                makeViews(sql)
                makeFunctions(sql)
        elif args.delete_user:
            sql.execute("SELECT Db FROM mysql.db WHERE User = %s;", (args.user))
            for db in sql.fetchall():
                db = db['Db']
                sql.execute("DROP DATABASE "+db.decode()+";") #The mysql.'tables' return b'' strings
            sql.execute("DROP USER '"+args.user+"'@'localhost'")

        elif args.delete:
            for db in args.db:
                login(user=args.user,passwd=args.password,database=db, test=True)
                #sql.execute("DELETE FROM dbases WHERE dbases.database = %s;",(db))
                sql.execute("DROP DATABASE "+db+";")
        logout(conn,sql)
            
    #print(args) #debug    


# %%bash
# #To save executable: first save notebook (Ctr-s), activate this cell (Ctr-m y), run (Ctr-Enter) and deactivate (Ctr-m t)
# 
# echo '#!/bin/env python' > MyFLdb.py
# ipython nbconvert --to python MyFLdb.ipynb --stdout >> MyFLdb.py
# chmod +x MyFLdb.py

