# Expand the template into multiple files, one for each item to be processed.
# 01-Jan to 30-June 0400-2059hrs, skipping Feb (we have no data there)
mkdir ./jobs
for m in {1..6}
do
    if [ $m = 2 ]
    then
        continue
    fi
    fold="2020$(printf %02d $m)"
    mkdir ./jobs/$fold

    for d in {1..31}
    do
        for H in {4..20}
        do
            a="2020$(printf %02d $m)$(printf %02d $d)-$(printf %02d $H)"
            cat job-tmpl.yaml | sed "s/\$ITEM/$a/" > ./jobs/$fold/job-$a.yaml
        done
    done
done