# Migrate your MySQL Database TO RDS MySQL

Mystique Unicorn App backend is hosted on mysql db. Recenly one of their devs discovered that AWS released Amazon RDS a fast, scalable, highly available, and fully managed relational database service that supports MySQL workloads.

Can you help them migrate from mysql hosted on prem(or EC2) to RDS MySQL?

## 🎯 Solutions

We will follow an multi-stage process to accomplish our goal. We need the following components to get this right,

1. **Source Database - MySQLDB**
   - If in AWS: EC2 instance in a VPC, Security Group, SSH Keypair(Optional)
   - Some dummy data inside the database
1. **Destination Database - RDS MySQL DB**
   - Subnet Groups
   - VPC Security Groups
1. **Database Migration Service(DMS) - Replication Instance**
   - DMS IAM Roles
   - Endpoints
   - Database Migration Tasks

![Miztiik Automation: Database Migration - MySQLDB to Amazon RDS MySQL DB](images/miztiik_architecture_mysql_to_rds_sql_db_01.png)

In this article, we will build an architecture, similar to the one shown above - A simple database running mysql(mariadb 10.2.x) instance running on EC2 _(You are welcome to use your own mysqldb instead_). For target we will build a Amazon RDS MySQL DB cluster and use DMS to migrate the data.

In this Workshop you will practice how to migrate your MySQLDB databases to Amazon RDS MySQL DB using different strategies.

1.  ## 🧰 Prerequisites

    This demo, instructions, scripts and cloudformation template is designed to be run in `us-east-1`. With few modifications you can try it out in other regions as well(_Not covered here_).

    - 🛠 AWS CLI Installed & Configured - [Get help here](https://youtu.be/TPyyfmQte0U)
    - 🛠 AWS CDK Installed & Configured - [Get help here](https://www.youtube.com/watch?v=MKwxpszw0Rc)
    - 🛠 Python Packages, _Change the below commands to suit your OS, the following is written for amzn linux 2_
      - Python3 - `yum install -y python3`
      - Python Pip - `yum install -y python-pip`
      - Virtualenv - `pip3 install virtualenv`

    As there are a number of components that need to be setup, we will use a combination of Cloudformation(generated from CDK), CLI & GUI.

1.  ## ⚙️ Setting up the environment

    - Get the application code

      ```bash
      git clone https://github.com/miztiik/mysql-to-rds
      cd mysql-to-rds
      ```

1.  ## 🚀 Prepare the environment

    We will need cdk to be installed to make our deployments easier. Lets go ahead and install the necessary components.

    ```bash
    # If you DONT have cdk installed
    npm install -g aws-cdk

    # Make sure you in root directory
    python3 -m venv .env
    source .env/bin/activate
    pip3 install -r requirements.txt
    ```

    The very first time you deploy an AWS CDK app into an environment _(account/region)_, you’ll need to install a `bootstrap stack`, Otherwise just go ahead and deploy using `cdk deploy`.

    ```bash
    cdk bootstrap
    cdk ls
    # Follow on screen prompts
    ```

    You should see an output of the available stacks,

    ```bash
    vpc-stack
    database-migration-prerequisite-stack
    mysql-on-ec2
    ```

1.  ## 🚀 Deploying the Source Database

    Let us walk through each of the stacks,

    - **Stack: vpc-stack**
      This stack will do the following,

      1. Create an custom VPC `miztiikMigrationVpc`(_We will use this VPC to host our source MySQLDB, RDS MySQL DB, DMS Replication Instance_)

      Initiate the deployment with the following command,

      ```bash
      cdk deploy vpc-stack
      ```

    - **Stack: database-migration-prerequisite-stack**
      This stack will create the following resources,

      1. RDS MySQL DB & DMS Security groups - (_created during the prerequisite stack_)
         - Port - `3306` _Accessible only from within the VPC_
      1. DMS IAM Roles - (This stack will **FAIL**, If these roles already exist in your account)
         - `AmazonDMSVPCManagementRole`
         - `AmazonDMSCloudWatchLogsRole`
      1. SSH KeyPair using a custom cfn resource
         - _This resource is currently not used. The intial idea was to use the SSH Keypair to administer the source MySql DB on EC2. [SSM Session Manager](https://www.youtube.com/watch?v=-ASMtZBrx-k) does the same job admirably._

      Initiate the deployment with the following command,

      ```bash
      cdk deploy database-migration-prerequisite-stack
      ```

      After successful completion, take a look at all the resources and get yourself familiar with them. We will be using them in the future.

    - **Stack: `mysql-on-ec2` Source Database - MySQLDB**
      This stack will do the following,

      1. Create an EC2 instance inside our custom VPC(_created during the prerequisite stack_)
      1. Attach security group with MySQL port(`3306`) open within the VPC (_For any use-case other than sandbox testing, you might want to restrict it_)
      1. Instance IAM Role is configured to allow SSM Session Manager connections(_No more SSH key pairs_)
      1. Instance is bootstrapped using `user_data` script to install `MariaDB 10.2.x`
      1. Create user `mysqladmin` & password (_We will need this later for inserts and DMS_)
      1. Creates a table `miztiik_db`(\_Later we will add a table `customers`)

      Initiate the deployment with the following command,

      ```bash
      cdk deploy mysql-on-ec2
      ```

      As our database is a fresh installation, it does not have any data in it. We need some data to migrate. This git repo also includes two files `create_database_table_on_mysql.py` and `insert_records_to_mysql.py` that will help us to generate some dummy data and insert them to the database. After successful launch of the stack,

      - Connect to the EC2 instance using SSM Session Manager - [Get help here](https://www.youtube.com/watch?v=-ASMtZBrx-k)
      - Switch to privileged user using `sudo su`
      - Navigate to `/var/log`
      - Run the following commands
        ```bash
        cd /var/log
        git clone https://github.com/miztiik/mysql-to-rds
        cd mysql_to_rds/mysql_to_rds/stacks/back_end/bootstrap_scripts
        python3 create_database_table_on_mysql.py
        # Make sure the create db and tales(previous step) completed successfully
        python3 insert_records_to_mysql.py
        ```
      - You should be able to observe records being _insert_ or _upsert_ to our database. The script logs a summary at the end,
        _Expected Output_,

        ```json
        [miztiik@ip-10-10-0-126 ~]# python3 /var/log/insert_records_to_mysql.py
        {"records_inserted":1000}
        ....
        ....
        {"records_inserted":41000}
        {"tot_of_records_inserted":41149}
        {"total_records_in_table": 90631}
        ```

        If you want to interact with mysql db, you can try out the following commands,

        ```bash
        # Open SQL shell
        # Password can be found in the userdata script
        mysql -h YOUR_EC2_PVT_IP -u root -p
        # List all Database
        show databases;
        # Use one of the datbases
        use miztiik_db;
        # List all tables
        show tables;
        # List 10 records from table customers
        use miztiik_db;SELECT * FROM customers LIMIT 10;
        # Show count of records in table custoemrs
        use miztiik_db;SELECT COUNT(*) FROM customers;
        # Quit
        exit;
        ```

        Now we are all done with our source database.

1.  ## 🚀 Deploying the Target Database - RDS MySQL DB

    We can automate the creation of RDS MySQL DB & DMS using CDK, But since this will be the first time we use these services,let us use the Console/GUI to set them up. We can leverage the excellant [documentation from AWS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.MySQL.html) on how to setup our RDS MySQL DB. (Use your best judgement, as docs tend to change over a period of time)

    Couple of things to note,

    - For VPC - Use our custom VPC `miztiikMigrationVpc`
    - For Security Group - Use `mysql_db_sg_database-migration-prerequisite-stack`

    Download the public key for Amazon RDS MySQL DB. We will need this to connect to RDS MySQL DB Cluster from your machine and also from DMS Replication Instance.

    ```bash
    wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
    ```

1.  ## 🚀 Deploying the DMS Replication Instance

    We can leverage the excellant [documentation from AWS](https://docs.aws.amazon.com/dms/latest/userguide/CHAP_GettingStarted.html) on how to setup our DMS Replication Instance.

    Couple of things to note,

    - For VPC - Use our custom VPC `miztiikMigrationVpc`
    - For Security Group - Use `dms_sg_database-migration-prerequisite-stack`

    After creating the replication instance, We need to create few more resources to begin our replication. We will use defaults mostly

    - **Endpoints for source MySQLDB**(_custom values listed below_)
      - Source choose mysqldb
      - For server address provide the private ip of the ec2 instance
      - Update username as `mysqladmin`, the password `Som3thingSh0uldBe1nVault`
      - Choose our custom VPC `miztiikMigrationVpc` and choose the DMS Replication instance we create in the previous step
    - **Endpoint for destination databases - RDS MySQL DB**(_custom values listed below_)
      - Choose Target endpoint
      - Check `Select RDS DB Instance`
      - Choose your RDS instance from the drop down list
      - Verify all the details of your RDS Instance
      - Choose our custom VPC `miztiikMigrationVpc` and choose the DMS Replication instance we create in the previous step
    - **Database Migration Task**
      - Choose our replication instance, source & destination endpoints
      - For Migration Type, choose `Migrate Existing Data and replicate ongoing changes`
      - Task Settings
        - Enable Validation
        - Enable CloudWatch Logs
      - For Table Mappings, _Add new selection rule_, you can create a custom schema name
        - For _Schema name_ write `miztiik_db`
        - For _Table name_ write `customers`
        - and Action `Include`
      - Create Task

1.  ## 🔬 Testing the solution

    Navigate to DMS task, under `Table Statistics` You should be able observe that the dms has copied the data from source to target database. You can connect to RDS MySQL DB and test the records using the same commands that we used with source earlier.

    ![Miztiik Automation: Database Migration - MySQLDB to Amazon RDS MySQL DB](images/miztiik_architecture_mysql_to_rds_sql_db_03.png)

    _Additional Learnings:_ You can check the logs in cloudwatch for more information or increase the logging level of the database migration task.

1.  ## 📒 Conclusion

    Here we have demonstrated how to use Amazon Database Migration Service(DMS) to migrate data from MySQLDB to RDS MySQL DB.

1.  ## 🎯 Additional Exercises

    - If your mysql database is small in size, you try to migrate using `mysqldump`. You can refer to this documentation[5]

    - Table storage optimization: To determine how fragmented a table is in MySQL, run a query like the following, and check the results for the data_free column, which will show the free space held by the table.

    ```sql
    SELECT table_name, data_length, max_data_length, index_length, data_free
    FROM information_schema.tables
    WHERE table_schema='schema_name';
    ```

1)  ## 🧹 CleanUp

    If you want to destroy all the resources created by the stack, Execute the below command to delete the stack, or _you can delete the stack from console as well_

    - Resources created during [Deploying The Application](#deploying-the-application)
    - Delete CloudWatch Lambda LogGroups
    - _Any other custom resources, you have created for this demo_

    ```bash
    # Delete from cdk
    cdk destroy

    # Follow any on-screen prompts

    # Delete the CF Stack, If you used cloudformation to deploy the stack.
    aws cloudformation delete-stack \
        --stack-name "MiztiikAutomationStack" \
        --region "${AWS_REGION}"
    ```

    This is not an exhaustive list, please carry out other necessary steps as maybe applicable to your needs.

## 📌 Who is using this

This repository aims to teach api best practices to new developers, Solution Architects & Ops Engineers in AWS. Based on that knowledge these Udemy [course #1][103], [course #2][102] helps you build complete architecture in AWS.

### 💡 Help/Suggestions or 🐛 Bugs

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional documentation or solutions, we greatly value feedback and contributions from our community. [Start here][200]

### 👋 Buy me a coffee

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q5Q41QDGK) Buy me a [coffee ☕][900].

### 📚 References

1. [How to install MariaDB][1]

1. [MySQLDB Dump Docs][2]

1. [Back Up and Restore MySQL Databases with Mysqldump][3]

1. [mysqldump — A Database Backup Program][4]

1. [mysqldump - blog][5]

1. [Automating mysql_secure_installation][6]

1. [Amazon Database Cost Optimisation][7]

### 🏷️ Metadata

![miztiik-success-green](https://img.shields.io/badge/Miztiik:Automation:Level-300-blue)

**Level**: 300

[1]: https://mariadb.com/resources/blog/installing-mariadb-10-on-centos-7-rhel-7/
[2]: https://mariadb.com/kb/en/mysqldump/
[3]: https://linuxize.com/post/how-to-back-up-and-restore-mysql-databases-with-mysqldump/
[4]: https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html
[5]: https://github.com/miztiik/aws-real-time-use-cases/tree/master/200-Storage-Migrate-To-RDS-DB
[6]: https://gist.github.com/Mins/4602864
[7]: https://aws.amazon.com/blogs/startups/scaling-down-your-infrastructure-part-2-cost-optimization/
[100]: https://www.udemy.com/course/aws-cloud-security/?referralCode=B7F1B6C78B45ADAF77A9
[101]: https://www.udemy.com/course/aws-cloud-security-proactive-way/?referralCode=71DC542AD4481309A441
[102]: https://www.udemy.com/course/aws-cloud-development-kit-from-beginner-to-professional/?referralCode=E15D7FB64E417C547579
[103]: https://www.udemy.com/course/aws-cloudformation-basics?referralCode=93AD3B1530BC871093D6
[200]: https://github.com/miztiik/api-with-stage-variables/issues
[899]: https://www.udemy.com/user/n-kumar/
[900]: https://ko-fi.com/miztiik
[901]: https://ko-fi.com/Q5Q41QDGK
