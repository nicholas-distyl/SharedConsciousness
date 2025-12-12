"""
ChatGPT Conversation Fetcher

Fetches conversations from ChatGPT using your browser session cookies.

Usage:
    1. Update the COOKIES dict below with fresh values from your browser
    2. Run: uv run fetch_chatgpt.py [conversation_id]

To get cookies:
    1. Open Chrome DevTools on chatgpt.com (F12)
    2. Go to Network tab
    3. Do any action (send a message or refresh)
    4. Right-click a request → Copy as cURL
    5. Extract the cookie values
"""
import requests
import json
import sys
from datetime import datetime


class ChatGPTClient:
    BASE_URL = "https://chatgpt.com"

    def __init__(self, cookies: dict):
        self.cookies = cookies
        self.headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "referer": "https://chatgpt.com/",
        }
        self.access_token = None

    def get_access_token(self) -> str | None:
        """Get access token from session endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/auth/session",
            cookies=self.cookies,
            headers=self.headers
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("accessToken")
            if self.access_token:
                self.headers["authorization"] = f"Bearer {self.access_token}"
            return self.access_token
        return None

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Fetch a conversation by ID."""
        if not self.access_token:
            self.get_access_token()

        response = requests.get(
            f"{self.BASE_URL}/backend-api/conversation/{conversation_id}",
            cookies=self.cookies,
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return None

    def list_conversations(self, limit: int = 20, offset: int = 0) -> dict | None:
        """List recent conversations."""
        if not self.access_token:
            self.get_access_token()

        response = requests.get(
            f"{self.BASE_URL}/backend-api/conversations",
            params={"limit": limit, "offset": offset},
            cookies=self.cookies,
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return None

    @staticmethod
    def extract_messages(conversation_data: dict) -> list[dict]:
        """Extract readable messages from conversation data."""
        messages = []
        mapping = conversation_data.get("mapping", {})

        for node_id, node in mapping.items():
            msg = node.get("message")
            if not msg:
                continue

            author = msg.get("author", {}).get("role", "unknown")
            content = msg.get("content", {})

            # Skip system messages that are hidden
            metadata = msg.get("metadata", {})
            if metadata.get("is_visually_hidden_from_conversation"):
                continue

            # Extract text content
            if content.get("content_type") == "text":
                parts = content.get("parts", [])
                text = "\n".join(str(p) for p in parts if p)
                if text.strip():
                    messages.append({
                        "id": node_id,
                        "role": author,
                        "content": text,
                        "create_time": msg.get("create_time"),
                        "parent": node.get("parent"),
                    })

        # Sort by create_time
        messages.sort(key=lambda m: m.get("create_time") or 0)
        return messages


# =============================================================================
# CONFIGURATION - Update these cookies with fresh values from your browser!
# =============================================================================
COOKIES = {
    "oai-did": "5e1bd3d4-0b25-424a-bad3-94e54a1a573b",
    "__Secure-next-auth.session-token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..JLboZ39TWscVNeEh.l59UVE-XT41lrpFcO69q1Mv2b301rFJ3yJFZo7lViGTRfIk46evnzSkvvwsQDp6ZdMJDpsAp8PcvA_zgc-u4iE5rW6S9IJQrNyhsIbpZAxHjhljjMRypHzsaitas0xaS0mzgH0joKnQT6FTXlvaeSPQglvhime9wPFF1w_6Ubs_sfkiCUoZu86padMQpAGXfko3VOvOmLBeFgkeiQnikksXodEGMXreC-Ekak-XAbRhauADgFfyYYIynb8WuJ9kISjlTy7yk3pQWD0Fuc-inGJi0vO3bk81HYtYRl2hTPoi8zlguUk3LsXKsVG_6aZlxKu-Ya_XUkhnux6I5ft1_IaPNgbYvVfeGxN0yj7apPfGAFYthMjOTgUqSZjjS3xpxkKCJUN6HeZScFZ2Zo3-9WDdMGeecKYDDZsRZ_Bs2L0hMNjMQrheDMsHs1fi5BYQ9ptd70V28S8N8GuqK9np_4KHHOEZ6DlDMueWhx8766sNqUZHipki3pqnf5NHa3U8nGLIaL8EeucNjFSk4zwHEJE90hsp_Mh8hrG2eJUnGFZI7swT7ALexXa0TgEUigWF2NIL5PhwMr4m7-6WgkaJEe3KrFZDLBa-OxBbH7qmiSEBGKCK1QES94lpqKlGfbQknsK2TezqboUNJlhW6jDJOsNYTSaCwZx9goByRRblu_coMrj7JWutwZ0onwxdCuJCSipIUD5AEF-u6xc3QqOG4lx7mSoFCnLsowuIpPpUSJ1FCwpGA4thDPDqp4umkDuXCTWs4LA8JEChK55TCv9WPaICnyen-7anDlXw_XeRl8ujY9E8Hre6w6DlvsSXoIGF4rV-vNO-nuSLjJoiQ8MsTLv5XvMJhsyGrHbUTd6bf-DC4dzAa57Py-TNmMILExBOBmL3jluzH35QbdX7-64JRes1y4SIYfspgjSpDqEAR1GD-na0TYcJ2vgcQk9h7qzUDuQ6hRkp2_UM5WW27EP69seDFK7Hs-fNZte-9PBI1thNYezSzV3LdaaA77lg03u3JEmHSwH2KUYYvS2iU8Oic35A57APSpnmZ5mTzYc7swGGQ4WEaq1l6k1ywJfeRlZ737ffspbpM3hRKZNzVtQqowdHOj_VYeFQOXN8XPHUcQL-j9V8TE6e4_tSATNHOyaIRY0XcfVGhz5lNBypyIX4aR0mN1VMCZmIGCCK3ZxAKMVVL6B-IJ8EiEMCIqXm6kakTvtSgEyNBQqOzyH60pLRwV7pqOQfk4G1dabMnV0Ajb42szLT0v8q4qPkZghR9bmE3Q3ok1Vuqb4f2Fxdl9gfhUwfBtH9rsJDVYB1AI1SIAmjNH9ffuS2FhIAPIyJI7uk4IDutSRKsdb7T7OooDbzonXe7_aXRB-BVWuxBUEAsUewZ7B2wWH73Y3flgSXWg_mPnVWpqG21VOrzk2hG2bnR7jMfS5_s6OULg5JFJrH4WZSBfTENzED7V1D9MVsts38g1RuDhcqxmLf3ndq08GnteCRYm64rctXqdr_YfIM-ITBQvgUeXorzp1G1OGeux5gRSeg-4tjIbQA18adhUE73Uh97ek-FRmVJN4U74i8Phq6js8GnjhsGo7D31fM7hnYq_KuR8tm4h5yPD_kp6JuNDlmSPNRvLWrIxi4M7qG982tNNCvXHATmxcboD4RUrIPoFk5q-9kT7n7ZVI8ff7FPpvhXi10l5x-udyuSo1bN6qx0Ui9Nv5BiSecbJYdog5-QtxF0DJwBxfOvmowKFXI5mpVxFAtjUyaAATMvjSdo22I98URzsUM1ChwgjSXdaZY0qL_6V4rXzqWZ0LH32yNJpq1Tla32AM_DNnuDEjrMh8OWMDWTdTbv8dHw0i8qx1h_nOurDz81jYXCCmrwP62tyzs6mtAtMioExHEOpIPIIooKwjFjizn1tqbc8ptc5iA0bnKcwSyILNNv-FnOqesnIMfX2Yq-8B_IIKYsMHKtOJGFyUkr2S1ziF6f7JZDXM6Z3GWUjPmoDuBPMjod60wtyq_4gJTM4LBH-0__p8_CNIqUl7RMdFjLXOkNPfVC0567E6E8UUQJRvVGplt8gYsR6ilpeOxGctq5nd-m2QoHXCTgXXrcsEPpRu1zzcWc0RUEAj2MrNWk5LfFHpsEMIE49u1OWeyEKFowbZ3jZcWJhO2L7zS0ZcJZc0slYgg0aIko4SoQNr3-d8SAd2LmQT7AkBZUXGyxExMzsDnbtSpT8q3JeozsfJnk-Pw9iA50CchWWPuampp_9koxj0HWRxntfaQrgdBSYDMJlT-nHmLqB0eb_M9ktPzRNl0fNFNnUpvHkPCSicHxOIsoqW25IsYW_7Mz1Wv6YALrQrl_yu5wi7WbzEY00tHjuN20fcjgpyEnHhzFZe4XYvVD4q1rRMmQMAS1ool0RhLSHXUg6TrGFY4Y_th0pKh_YVUtQjfcgyaGkyV8hv74liUE4ER_gmltJpCroJljast__vgAXguYbdFxt5C3W8pGFEcfhy803I9sxbpd3HGBXW5qLTFB1oziKzqA6wryKH80nZwO_vkUy9KgmSKykHrP-0qDnX0lNGS0jqOd234krwAw8gakXKsOCygLxWpR43Bk0wbfLxRoxs1nzKkWQD2tNE1IItXrXsyxX9ekviDb4cz607j_h7G_zpIf5IJPkJTXqa4YFWFIetjG8-K41-dnLWQf_Vnv90tpTWa_CFyjGx8ZGioReqn0cVaox2LpeCDn69Huty7Luev-hmmBEb8kMoT4Ls9W3Z76rR1OyDC5uvjOBzbpCsp4GX6rz53CaZoRZicSaBN0ILS9qTWaspxDrpSUpIrcZ6yiqQK-emltN3lvBvsSXBeHMqFOxiKqSz48_48sQlonk3wOnbelkV2Jzasz38iXZYELZ8w36EFilQwHr5LPgeiF2amSaro-FweWN0JmbmJ2PyWcgUbK6V5xjxiE8ahO1Yyf2v_7XtOSo46cuoBDA6ytvZA_pKDqoAeOPcJiZ6861yWckDRtSkStNn4UGfCZn2PniUM964VfHDd_DCkzRiCRmw5Ot1xug_yVukKqFsvcCRUfoKmQE1Nyrnzpc-qjqwdaagNOjzeX6dM9KyqS5rydRkdnIfxXqgPcWE90nt-Tc2agrm_MkiHmhtD_v0u-usokgkJRiNQE_L1E-vpwzzvVyclxa8T2dmpG9HOpZw48-mPUzrWPxBMBqv2QopZtFZKf3r0MXAAiQwAd7GAB2fqFnl7ZdA512oUWDMotDjWwejyP3OktmrmOjwmfM5KJsU1A0PghVFgbxtegVTr4sgUck093ZGlEZ2hmGW1tX2OpHNA8KAnqi3cmvTIbe8KaT68gyXv93smBmkPJdfwb46S_c-DIX4StRkHKaDFvva3s1OE-6RAVW-qBCn6OJMNcAVAjsAEHrPW4pWoMpjd3h7xJ5mJoRy2k8v6c3vuf37KTzyh3FXF4NCeFjhWgMarOkb6mXrJTX2aboGK6L06T7zFgv5gNdacZeNd21hOJzdVI1g3_KWJ0LtOvo8P7EZHFRDhewgF6lrTk8IWAR_mj4XQ9zdpOxiK2dsYwriFm4F-N3RHw3Xo00MV4us2RW25QwmUAUPHIT8XH6BqJ2skg1jLcjpwJHavvR1fzKKq3losVvHsV5BqzRoTNrDfRUeHhuz-1J5XLxG66RhMN-BOVaPDWd6BvpSu7KUG5.QoNhGTo1JlagDeqVXQXaKw",
    "_puid": "user-PSRQd6uO4MJ3G7IlARuIq8xC:1765396084-zwA6vKnVvCVGFDn0lPDEu4ucOoS4N5ltnJMPCqeMnSM%3D",
    "oai-sc": "0gAAAAABpOdJE_hJPR20WxRJ78Guuf0h_oBdzh9u2J0k8JV9R_OeM89p_Ap-8biYuB_AK9dG_UrGW6hZraFDD07eL4vPLdAsnjzXa86Mr0rTwvFPkhDYPvzhkETdM4oVlEPes-h6foW5blInP2nR4g1dVPQ36nsPWerLLys8Xe5IgMU63Qu_zgZiIVLCRdZIcGmlLfGxnzCyJmh0jV4DHMhWa_jjHx8FgfoGF00sijZUDQj3SaxCoCSA",
    "_account": "f19f08a0-d570-4633-b9bc-a3513ba997a8",
}


def main():
    # Default conversation ID (the one you wanted to fetch)
    conversation_id = "69399ea2-f73c-832f-9de1-7a39cf246efc"

    # Allow override via command line
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]

    print("ChatGPT Conversation Fetcher")
    print("=" * 50)

    client = ChatGPTClient(COOKIES)

    # Get access token
    print("Authenticating...")
    token = client.get_access_token()
    if not token:
        print("ERROR: Failed to get access token. Cookies may be expired.")
        print("Please update the COOKIES dict with fresh values from your browser.")
        sys.exit(1)
    print("Authenticated successfully!")
    print()

    # Fetch conversation
    print(f"Fetching conversation: {conversation_id}")
    data = client.get_conversation(conversation_id)

    if not data:
        print("ERROR: Failed to fetch conversation.")
        sys.exit(1)

    # Display conversation info
    print(f"Title: {data.get('title', 'Untitled')}")
    print()

    # Extract and display messages
    print("Messages:")
    print("-" * 50)
    messages = client.extract_messages(data)

    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]

        # Format timestamp
        ts = msg.get("create_time")
        time_str = ""
        if ts:
            time_str = f" [{datetime.fromtimestamp(ts).strftime('%H:%M:%S')}]"

        print(f"\n[{role}]{time_str}")
        print(content[:500] + ("..." if len(content) > 500 else ""))

    print()
    print("-" * 50)
    print(f"Total messages: {len(messages)}")

    # Save raw data to file
    output_file = f"conversation_{conversation_id}.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Raw data saved to: {output_file}")


if __name__ == "__main__":
    main()
