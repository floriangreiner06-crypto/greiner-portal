#!/bin/bash
# ============================================================================
# PATCH FÜR CHEF-ÜBERSICHT - TAG 103
# ============================================================================
# Fügt die Chef-API und Route zur app.py hinzu
# ============================================================================

APP_FILE="/opt/greiner-portal/app.py"

# 1. Chef-API Blueprint registrieren (nach vacation_api)
grep -q "vacation_chef_api" $APP_FILE
if [ $? -ne 0 ]; then
    sed -i '/^from api.vacation_api import vacation_api$/a\
# Vacation Chef API (TAG 103)\
try:\
    from api.vacation_chef_api import chef_api\
    app.register_blueprint(chef_api)\
    print("✅ Vacation Chef API registriert: /api/vacation/chef-overview")\
except Exception as e:\
    print(f"⚠️  Vacation Chef API nicht geladen: {e}")' $APP_FILE
    echo "✅ Chef-API hinzugefügt"
else
    echo "ℹ️  Chef-API bereits vorhanden"
fi

# 2. Chef-Übersicht Route hinzufügen (nach urlaubsplaner_v2)
grep -q "urlaubsplaner_chef" $APP_FILE
if [ $? -ne 0 ]; then
    sed -i '/^def urlaubsplaner_v2():$/,/return render_template.*urlaubsplaner_v2.html/a\
\
# Urlaubsplaner Chef-Übersicht (TAG 103)\
@app.route("/urlaubsplaner/chef")\
@login_required\
def urlaubsplaner_chef():\
    """Chef-Übersicht: Alle Teams und Genehmiger"""\
    return render_template("urlaubsplaner_chef.html")' $APP_FILE
    echo "✅ Chef-Route hinzugefügt"
else
    echo "ℹ️  Chef-Route bereits vorhanden"
fi

echo "✅ Patch abgeschlossen"
