# app.py
from datetime import date, timedelta
import math
import streamlit as st
import qrcode

Bootspauschalen = {"Wiking": 102, "Frithjof": 36, "Sprotte": 36}

Beitragsstufen = {
    "OM": "I",
    "AOM": "II",
    "ADAH": "II",
    "OM (VASV)": "I",
    "AOM (VASV)": "II",
    "ADAH (VASV)": "II",
    "Gast, Student/Schüler/Azubi": "II",
    "anderer Gast": "III",
}

Beitragsstufenaufschläge = {
    "I Wiking": 0,
    "II Wiking": 23,
    "III Wiking": 33,
    "I Frithjof": 0,
    "II Frithjof": 13,
    "III Frithjof": 23,
    "I Sprotte": 0,
    "II Sprotte": 13,
    "III Sprotte": 23,
}


class Trip:
    def __init__(self) -> None:
        # input data from trip section
        self.description = ""
        self.boat = ""
        self.first_day = date.today()
        self.last_day = date.today() + timedelta(days=14)
        self.number_of_participants = 0
        # data derived from trip section
        self._number_of_nights = 0
        self._boat_rate = 0
        self._max_boat_total = 0
        # input data from participants section
        self.participants = []
        # data derived from participants section
        self._participants_nights = 0
        self._participants_nights_om = 0
        self._boat_rate_by_participant_night = 0
        self._is_skipper_discount_entitled = False
        self._total = 0
        # input data from skipper section
        self.skipper = ""
        self.skipper_IBAN = ""
        self.skipper_BIC = ""
        self.is_skipper_discount_desired = False

    def __str__(self):
        return f"({self.description},{self.boat},{self.first_day},{self.last_day},{self.number_of_participants},{self.number_of_nights},{self.boat_rate},{self.max_boat_total},{self.participants_nights},{self.participants_nights_om},{self.boat_rate_by_participant_night},{self.is_skipper_discount_entitled},{self.total},{self.skipper},{self.skipper_IBAN},{self.skipper_BIC},{self.is_skipper_discount_desired})"

    @property
    def number_of_nights(self):
        return (self.last_day - self.first_day).days

    @property
    def boat_rate(self):
        return Bootspauschalen.get(self.boat)

    @property
    def max_boat_total(self):
        return self.boat_rate * self.number_of_nights

    @property
    def participants_nights(self):
        return sum([participant.number_of_nights for participant in self.participants])

    @property
    def participants_nights_om(self):
        return sum(
            [participant.number_of_nights_om for participant in self.participants]
        )

    @property
    def boat_rate_by_participant_night(self):
        return self.max_boat_total / self.participants_nights

    @property
    def total(self):
        return sum([participant.boat_total for participant in self.participants]) + sum(
            [participant.extra_total[0] for participant in self.participants]
        )

    @property
    def is_skipper_discount_entitled(self):
        if self.participants_nights_om / self.participants_nights >= 0.5:
            return True
        else:
            return False


class Participant(Trip):
    def __init__(self, trip) -> None:
        # input data from participants section
        self.name = ""
        self.type = ""
        self.first_day = trip.first_day
        self.last_day = trip.last_day
        # data derived from participants section
        self._number_of_nights = 0
        self._number_of_nights_om = 0
        self._rate_group = ""
        self._extra_rate = 0
        # this is a tuple which returns a foot note as second item in case skipper discount is applied
        self._extra_total = 0, ""
        self._boat_total = 0
        # data derived from trip section
        self.trip = trip

    def __str__(self):
        return f"({self.name},{self.type},{self.first_day},{self.last_day},{self.number_of_nights},{self.number_of_nights_om},{self.rate_group},{self.extra_rate},{self.extra_total},{self.boat_total})"

    @property
    def number_of_nights(self):
        return (self.last_day - self.first_day).days

    @property
    def number_of_nights_om(self):
        if self.type == "OM":
            return self.number_of_nights
        else:
            return 0

    @property
    def rate_group(self):
        return Beitragsstufen.get(self.type)

    @property
    def extra_rate(self):
        return Beitragsstufenaufschläge.get(self.rate_group + " " + self.trip.boat)

    @property
    def extra_total(self):
        # this is a tuple which returns a foot note as second item in case skipper discount is applied
        if (
            self.trip.skipper == self.name
            and self.trip.is_skipper_discount_entitled
            and self.trip.is_skipper_discount_desired
        ):
            return (self.number_of_nights * 0), "(*)"
        else:
            return (self.number_of_nights * self.extra_rate), ""

    @property
    def boat_total(self):
       return round_up(
            self.number_of_nights * self.trip.boat_rate_by_participant_night)


def round_up(n):
    # round up to second decimal
    return math.ceil(n * 100) / 100


def round_normal(n):
    # round second decimal to #.#0 for #.#00 to #.#04 and to #.#1 for #.#05 to #.#09
    return math.floor(n * 100 + 0.5) / 100


def app(rate_groups, boat_rates, extra_rates):
    # browser tab title & favicon
    st.set_page_config(
        page_title="ASVzL Törnbeitragsrechner", page_icon=":boat:")

    # page title & header
    st.title("Törnbeitragsrechner", "section-1")
    st.write(
        "Die App speichert keinerlei Daten, weshalb Eingaben und Ergebnisse nur bis zur Beendigung der Browser Sitzung zur Verfügung stehen."
    )
    st.markdown("[Gebührenordnung >](#section-2)", unsafe_allow_html=True)

    # input trip data
    trip = Trip()
    trip.description = st.text_input(
        "Törnbezeichnung / Verwendungszweck in Überweisung an Schatzmeister",
        value=trip.description,
        placeholder="z.B. Sommertörn 2022 - Skipper John Doe",
    )

    trip_col1, trip_col2, trip_col3, trip_col4 = st.columns(4)

    trip.boat = trip_col1.selectbox("Boot", boat_rates.keys())
    # boat_rate = boat_rates.get(boat)
    trip.first_day = trip_col2.date_input(
        "Reisedatum von", value=trip.first_day)

    trip.last_day = trip_col3.date_input(
        "Reisedatum bis",
        value=trip.first_day + timedelta(days=14), min_value=trip.first_day + timedelta(days=1))

    trip_col4.write("Anzahl Nächte\n\n" + str(trip.number_of_nights))
    # check trip duration
    if trip.number_of_nights > 20:
        st.warning(
            "Prüfe bitte ob eine Reisedauer von "
            + str(trip.number_of_nights)
            + " Nächten stimmen kann."
        )

    st.info(
        "Die Bootspauschale für den Törn beträgt : "
        + str(trip.boat_rate)
        + " € x "
        + str(trip.number_of_nights)
        + " Nächte = "
        + str(trip.max_boat_total)
        + " €"
    )

    trip.number_of_participants = st.selectbox(
        "Anzahl Teilnehmer", (2, 3, 4, 5, 6, 7, 8)
    )
    # print(trip)

    # input data for every participant
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    p_col1.caption("Teilnehmer Name")
    p_col2.caption("Teilnehmer Typ")
    p_col3.caption("Reisedatum von")
    p_col4.caption("Reisedatum bis")

    for i in range(trip.number_of_participants):
        p = Participant(trip)
        default_name = "Jane Doe " + str(i + 1)

        p.name = p_col1.text_input("", value=default_name, key="name" + str(i))
        trip.participants.append(p)

        # check for duplicate participant name
        participant_names = [
            participant.name for participant in trip.participants]
        if participant_names.count(p.name) > 1:
            st.warning(
                "Teilnehmer Name wird bereits verwendet. Namen müssen einzigarting sein, damit die App funktioniert!"
            )
            st.stop()

        p.type = p_col2.selectbox("", rate_groups.keys(), key="type" + str(i))

        p.first_day = p_col3.date_input(
            "",
            value=p.first_day,
            min_value=trip.first_day,
            max_value=trip.last_day - timedelta(days=1),
            key="first_day"+str(i)
        )

        p.last_day = p_col4.date_input(
            "",
            value=p.last_day,
            min_value=p.first_day + timedelta(days=1),
            max_value=trip.last_day,
            key="last_day"+str(i)
        )

        trip.participants[i] = p

    st.info(
        "Bootspauschale je Teilnehmer pro Nacht beträgt: "
        + str(trip.max_boat_total)
        + " € / "
        + str(trip.participants_nights)
        + " Teilnehmernächte = "
        + "{:.2f}".format(trip.boat_rate_by_participant_night)
        + " €"
    )

    # input skipper data
    trip.skipper = st.selectbox(
        "Skipper Name, für Überweisungs-QR-Code bitte oben vollständig eingeben!",
        participant_names,
    )
    trip.skipper_IBAN = st.text_input("Skipper IBAN")
    trip.skipper_BIC = st.text_input("Skipper BIC")
    if trip.is_skipper_discount_entitled:
        st.info(
            str(trip.participants_nights_om)
            + " 'OM' Nächte / "
            + str(trip.participants_nights)
            + " Teilnehmer Nächte = "
            + "{:.0f}".format(
                trip.participants_nights_om / trip.participants_nights * 100
            )
            + "%\n\nSkipper ist nicht verpflichtet den Aufschlag zu zahlen, da mindestens die Hälfte der Übernachtungen auf 'OM' entfallen."
        )
        skipper_radio_button = st.radio(
            "Möchte der Skipper die Befreiung vom Aufschlag in Anspruch Anspruch nehmen? Dieser darf im nachherein gerne gespendet werden.",
            ("Ja", "Nein"),
            index=1,
            horizontal=True,
        )
    if skipper_radio_button == "Ja":
        trip.is_skipper_discount_desired = True
    else:
        trip.is_skipper_discount_desired = False

    # output result data for every participant
    p_col1, p_col2, p_col3, p_col4, p_col5, p_col6 = st.columns(6)
    p_col1.caption("Teilnehmer")
    p_col2.caption("Beitragsstufe")
    p_col3.caption("Aufschlagsatz")
    p_col4.caption("Bootssatz")
    p_col5.caption("Nächte")
    p_col6.caption("Törnbeitrag")
    for i in range(trip.number_of_participants):
        p = trip.participants[i]
        p_col1.text(p.name)
        p_col2.text(p.rate_group)
        p_col3.text("{:.2f}".format(p.extra_rate) + p.extra_total[1])
        p_col4.text("{:.2f}".format(trip.boat_rate_by_participant_night))
        p_col5.text(p.number_of_nights)
        p_col6.text("{:.2f}".format(p.extra_total[0] + p.boat_total) + p.extra_total[1])

    if skipper_radio_button == "Ja":
        trip.is_skipper_discount_desired = True
        st.write("Mit (*) markierte Zeile berücksichtigt Skipper Befreiung vom Aufschlag.")
    else:
        trip.is_skipper_discount_desired = False


    st.subheader("QR-Codes zur Überweisung der Törnbeiträge")
    st.write("Erfolgreich getestet mit ING und Postbank.")

    # create QR-code for money transfer to skipper
    dateiname = "epc_qr.png"
    empfänger = trip.skipper
    iban = trip.skipper_IBAN
    bic = trip.skipper_BIC

    for i in range(trip.number_of_participants):
        p = trip.participants[i]
        if p.name != trip.skipper:
            vwz = p.name + " - " + trip.description
            betrag = "{:.2f}".format(p.boat_total + p.extra_total[0])

            qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5
            )

            qr.add_data("BCD\n")
            qr.add_data("002\n")
            qr.add_data("1\n")
            qr.add_data("SCT\n")
            qr.add_data(bic + "\n")
            qr.add_data(empfänger[0:69] + "\n")
            qr.add_data(iban + "\n")
            qr.add_data("EUR" + betrag + "\n")
            qr.add_data("\n")
            qr.add_data("\n")
            qr.add_data(vwz[0:139] + "\n")
            qr.make(fit=True)
            img = qr.make_image()
            img.save(dateiname)

            st.image(
                dateiname,
                caption="QR-Code für " + p.name + " zur Überweisung an den Skipper",
            )
            st.write("Empfänger: " + empfänger)
            st.write("IBAN: " + iban)
            st.write("BIC: " + bic)
            st.write("Betrag: " + str(betrag))
            st.write("Verwendungszweck: " + vwz)

    # create QR-code for money transfer to club
    empfänger = "Akademischer Seglerverein zu Luebeck e.V."
    vwz = trip.description
    iban = "DE49230501010003300050"
    bic = "NOLADE21SPL"
    betrag = "{:.2f}".format(trip.total)

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5)

    qr.add_data("BCD\n")
    qr.add_data("002\n")
    qr.add_data("1\n")
    qr.add_data("SCT\n")
    qr.add_data(bic + "\n")
    qr.add_data(empfänger[0:69] + "\n")
    qr.add_data(iban + "\n")
    qr.add_data("EUR" + betrag + "\n")
    qr.add_data("\n")
    qr.add_data("\n")
    qr.add_data(vwz[0:139] + "\n")
    qr.make(fit=True)
    img = qr.make_image()
    img.save(dateiname)

    st.image(dateiname, caption="QR-Code für Skipper zur Überweisung an den Verein")
    st.write("Empfänger: " + empfänger)
    st.write("IBAN: " + iban)
    st.write("BIC: " + bic)
    st.write("Betrag: " + str(betrag))
    st.write("Verwendungszweck: " + vwz)

    st.title("Gebührenordnung", "section-2")
    st.markdown("[nach oben >](#section-1)", unsafe_allow_html=True)

    """
    ## Beitragsstufen

    >I: OM

    >II: ADAH, AOM, vereinslose studentische Gäste

    >III: vereinslose nicht-studentische Gäste

    ## Bootspauschalen / Aufschläge

    >  ### Wiking

    >>Bootspauschale je Nacht: 102€

    >>Beitragsstufenaufschlag je Nacht: I: -, II: 23 €, III: 33 €

    >  ### Frithjof / Sprotte

    >>Bootspauschale je Nacht: 36 €

    >>Beitragsstufenaufschlag je Nacht: I: -, II: 13 €, III: 23 €

    ## Regeln
    * Jedem Teilnehmer wird eine Beitragsstufe zugeordnet.
    * Schüler, Auszubildende und Doktoranden werden wie Studenten eingestuft.
    * Gästen von anderen Vereinen im VASV wird die entsprechende Beitragsstufe wie Mitglieder zugeordnet.
    * Je Übernachtung wird an den Schatzmeister die Bootspauschale plus die Aufschläge gemäß Beitragsstufe abzüglich eines eventuellen Skipperrabatts durch den Skipper abgeführt.
    * Jeder Teilnehmer trägt den gleichen Anteil an der Bootspauschale.
    * Jeder Teilnehmer zahlt zusätzlich einen Aufschlag entsprechend seiner Beitragsstufe.
    * Entfallen mehr als 50 % der Summe der Teilnehmerübernachtungen auf OM, darf der Skipper seinen Beitrag halbieren.
    """


if __name__ == "__main__":
    app(Beitragsstufen, Bootspauschalen, Beitragsstufenaufschläge)
